from brigitte.repositories.models import Repository
from brigitte.accounts.models import SshPublicKey

from brigitte.repositories.backends.base import ShellMixin

import os

def generate_gitolite_conf(file_path):
    file_obj = open(file_path, 'w')

    lines = [
        'repo    gitolite-admin\n',
        '\tRW+     =   gitolite\n',
    ]

    def generate_access_rule(repo_user, key):
        if repo_user.can_write and key.can_write:
            return 'RW+'
        elif repo_user.can_read and key.can_read:
            return 'R'

    for repo in Repository.objects.all():
        keys = []
        for user in repo.repositoryuser_set.all():
            for key in user.user.sshpublickey_set.all():
                keys.append('\t%s\t= key-%s\n' % (generate_access_rule(user, key), key.pk))

        if len(keys) > 0:
            lines.append('\n')
            lines.append('repo\t%s\n' % repo.short_path[:-4])
            lines.extend(keys)

    file_obj.writelines(lines)
    file_obj.close()

def export_public_keys(keydir_path):
    for key in os.listdir(keydir_path):
        key_path = os.path.join(keydir_path, key)
        if os.path.isfile(key_path) and key != 'gitolite.pub':
            os.unlink(key_path)

    for pubkey in SshPublicKey.objects.all():
        key_obj = open(os.path.join(keydir_path, 'key-%s.pub' % pubkey.pk), 'w')
        key_obj.write('%s\n' % pubkey.key)
        key_obj.close()

def update_gitolite_repo(gitolite_path):
    commands =  [
        'git add .',
        'git commit -q -m updated -a',
        'git push -q',
    ]

    shell = ShellMixin()

    for command in commands:
        shell.exec_command(['/bin/sh', '-c', 'cd "%s"; %s' % (gitolite_path, command)])

