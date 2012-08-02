# -*- coding: utf-8 -*-
import os
import shlex
import sys
from twisted.conch.avatar import ConchUser
from twisted.conch.checkers import SSHPublicKeyDatabase
from twisted.conch.ssh import common
from twisted.conch.ssh.factory import SSHFactory
from twisted.conch.ssh.keys import Key
from twisted.conch.ssh.session import (ISession, SSHSession,
    SSHSessionProcessProtocol)
from twisted.cred.portal import IRealm, Portal
from twisted.internet import reactor
from twisted.python import log
from zope import interface

from django.contrib.auth.models import User

from brigitte.accounts.models import SshPublicKey
from brigitte.repositories.models import Repository, RepositoryUser


log.startLogging(sys.stderr)


def find_git_shell():
    # Find git-shell path.
    # Adapted from http://bugs.python.org/file15381/shutil_which.patch
    path = os.environ.get("PATH", os.defpath)
    for dir in path.split(os.pathsep):
        full_path = os.path.join(dir, 'git-shell')
        if (os.path.exists(full_path)
            and os.access(full_path, (os.F_OK | os.X_OK))):
            return full_path
    raise Exception('Could not find git executable!')

class GitSession(object):
    interface.implements(ISession)

    def __init__(self, user):
        self.user = user

    def writeErr(self, proto, message):
        proto.session.writeExtended(1, ('%s\n' % message).encode('UTF-8'))

    def execCommand(self, proto, cmd):
        self.writeErr(proto, 'Welcome to Brigitte.')

        argv = shlex.split(cmd)

        repo_url = argv[-1].strip('/')
        repo = self.get_repo(repo_url)

        close_connection = True
        if not repo:
            self.writeErr(proto, 'Invalid repository: %s' % repo_url)
        else:
            self.writeErr(proto, 'Trying to access repository: %s' % repo.slug)
            if self.validate_git_command(proto, argv, repo):
                close_connection = False
                self.execute_git_command(proto, argv, repo)

        if close_connection:
            proto.loseConnection()

    def validate_git_command(self, proto, argv, repo):
        command = argv[0]

        if command not in (
            'git-upload-archive',
            'git-receive-pack',
            'git-upload-pack'
        ):
            self.writeErr(proto, 'Invalid command: %s' % command)
            return False
        else:
            # upload means receive, weird.
            want_write = not 'upload' in command
            self.writeErr(proto,
                'Attempted access: %s' % ('write' if want_write else 'read'))

            db_user = User.objects.get(username=self.user.username)
            try:
                access = repo.repositoryuser_set.get(user__username=db_user)
            except RepositoryUser.DoesNotExist:
                self.writeErr(proto,
                    'No access configuration found for %s' % db_user.username)
                return False

            self.writeErr(proto, 'Access for %s - read: %s write: %s' % (
                db_user.username, access.can_read, access.can_write))

            if ((want_write and not access.can_write)
                or (not want_write and not access.can_read)):
                self.writeErr(proto, 'Access denied!')
                return False

            return True

    def execute_git_command(self, proto, argv, repo):
        sh = self.user.shell
        command = ' '.join(argv[:-1] + ["'%s'" % (repo.path,)])
        reactor.spawnProcess(proto, sh,(sh, '-c', command))

    def eofReceived(self):
        pass

    def closed(self):
        pass

    def get_repo(self, reponame):
        log.msg('looking up repository %s' % reponame)

        username, slug = reponame.strip('/').split('/', 1)
        slug = slug.rsplit('.', 1)[0]

        try:
            repo = Repository.objects.get(
                repositoryuser__user__username=username, slug=slug)
            return repo
        except Repository.DoesNotExist:
            return None

class GitPubKeyChecker(SSHPublicKeyDatabase):
    def get_pub_keys(self):
        log.msg('loading availble public keys')
        return list(SshPublicKey.objects.values_list('user__username', 'key'))

    def checkKey(self, credentials):
        log.msg('checking key..')
        for username, user_key in self.get_pub_keys():
            log.msg('testing key from user %s' % username)
            if Key.fromString(user_key).blob() == credentials.blob:
                log.msg('found key for user %s' % username)
                credentials.username = username
                return True
        return False

# Backport: http://twistedmatrix.com/trac/ticket/5142
class GitProcessProtocolSession(SSHSession):
    def request_exec(self, data):
        if not self.session:
            self.session = ISession(self.avatar)
        f, data = common.getNS(data)
        log.msg('executing command "%s"' % f)
        try:
            pp = GitProcessProtocol(self)
            self.session.execCommand(pp, f)
        except:
            log.deferr()
            return 0
        else:
            self.client = pp
            return 1

# Backport: http://twistedmatrix.com/trac/ticket/5142
class GitProcessProtocol(SSHSessionProcessProtocol):
    def __init__(self, session):
        self.session = session
        self.lostOutFlag = False
        self.lostErrFlag = False

    def outConnectionLost(self):
        if self.lostOutFlag and self.lostErrFlag:
            self.session.conn.sendEOF(self.session)
        else:
            self.lostOutOrErrFlag = True
        self.lostOutFlag = True

    def errConnectionLost(self):
        self.lostErrFlag = True

class GitConchUser(ConchUser):
    shell = find_git_shell()

    def __init__(self, username):
        ConchUser.__init__(self)
        self.username = username
        self.channelLookup.update({"session": GitProcessProtocolSession})

    def logout(self):
        pass

class GitRealm(object):
    interface.implements(IRealm)

    def requestAvatar(self, username, mind, *interfaces):
        user = GitConchUser(username)
        return interfaces[0], user, user.logout

class GitServer(SSHFactory):
    portal = Portal(GitRealm())
    portal.registerChecker(GitPubKeyChecker())

    def __init__(self, priv_key):
        pub_key = '%s.pub' % priv_key
        self.privateKeys = {'ssh-rsa': Key.fromFile(priv_key)}
        self.publicKeys = {'ssh-rsa': Key.fromFile(pub_key)}
