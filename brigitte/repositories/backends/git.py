# -*- coding: utf-8 -*-
import re
import os
import operator
import shutil
from datetime import datetime
from django.conf import settings
import cStringIO

from dulwich.repo import Repo as DulwichRepo

from django.core.cache import cache

from brigitte.repositories.backends.base import BaseRepo, BaseCommit
from brigitte.repositories.backends.base import BaseTag, BaseBranch
from brigitte.repositories.backends.base import BaseFile, BaseTree


AUTHOR_EMAIL_RE=re.compile('(.*) <(.*)>')

FILETYPE_MAP = getattr(settings, 'FILETYPE_MAP', {})


TREE_RE = re.compile(
    "(?P<rights>\d*)\s(?P<type>[a-z]*)"
    "\s(?P<sha>\w*)\s*(?P<size>[0-9 -]*)\s*(?P<path>.+)")

FILE_RE = re.compile("\.\w+")
HUNK_RE = re.compile(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@')


class Repo(BaseRepo):
    def __getstate__(self):
        state = self.__dict__.copy()
        # Dulwich Repo is not cachable
        if '_git_repo' in state:
            del state['_git_repo']
        return state

    @property
    def git_repo(self):
        if not hasattr(self, '_git_repo'):
            self._git_repo = DulwichRepo(self.path)
        return self._git_repo

    def get_refs(self, ref_type):
        # we only support heads and tags
        assert ref_type in ('heads', 'tags')

        # sadly, tags and commits have different attributes for the time
        time_attr = 'commit_time' if ref_type == 'heads' else 'tag_time'

        ref_prefix_len = 6 + len(ref_type)

        for ref, sha in self.git_repo.get_refs().iteritems():
            if ref[:ref_prefix_len] == 'refs/%s/' % ref_type:
                commit = self.git_repo[sha]
                # only return refs with valid time attribute
                if hasattr(commit, time_attr):
                    yield (ref[ref_prefix_len:], sha, getattr(commit, time_attr))

    @property
    def tags(self):
        return [Tag(self, tag, sha)
            for tag, sha, time
            in sorted(self.get_refs('tags'), key=operator.itemgetter(2), reverse=True)
        ]

    @property
    def branches(self):
        return [Branch(self, branch, sha)
            for branch, sha, time
            in sorted(self.get_refs('heads'), key=operator.itemgetter(2), reverse=True)
        ]

    def resolve_head(self, head):
        try:
            return self.git_repo.ref('refs/heads/%s' % head)
        except KeyError:
            return self.git_repo.ref('refs/tags/%s' % head)

    def _get_commit_list(self, sha=None, count=10, skip=0, head=None, path=None):
        if sha == None:
            try:
                sha = self.resolve_head(head) if head else self.git_repo.head()
            except KeyError:
                # no commits and no head found
                return []

        paths = [path] if path else None

        commits = []

        for entry in list(self.git_repo.get_walker(
            include=[sha], max_entries=count+skip, paths=paths))[skip:]:

            author = AUTHOR_EMAIL_RE.match(entry.commit.author).groups(0)
            committer = AUTHOR_EMAIL_RE.match(entry.commit.committer).groups(0)

            commits.append(Commit(self, {
                'id': entry.commit.id,
                'tree': entry.commit.tree,
                'parents': entry.commit.parents,
                'short_message': entry.commit.message.split('\n')[0],
                'message': entry.commit.message,
                'timestamp': entry.commit.commit_time,
                'author': author[0],
                'author_email': author[1],
                'committer': committer[0],
                'committer_email': committer[1],
            }))

        return commits

    def get_commits(self, count=10, skip=0, head=None, path=None):
        return self._get_commit_list(
            sha=None, count=count, skip=skip, head=head, path=path)

    def get_commit(self, sha, path=None):
        cache_key = '%s:commit:%s:%s' % (self.repo.pk, sha, path or 'direct')

        commit = None

        if sha:
            commit = cache.get(cache_key)

        if not commit:
            try:
                commit = self._get_commit_list(sha=sha, count=1, skip=0, path=path)[0]
            except IndexError:
                pass

            if sha and commit:
                cache.set(cache_key, commit, 2592000)

        return commit

    @property
    def last_commit(self):
        return self.get_commit(None)

    def init_repo(self):
        cmd = 'git init -q --shared=0770 --bare %s --template=%s/%s' % (
            self.path, settings.PROJECT_ROOT, 'repo_templates/git/')
        self.exec_command(cmd)
        return True

    def path_exists(self, slug):
        if os.path.exists(os.path.join(
            settings.BRIGITTE_GIT_BASE_PATH, '_trash', '%s.git' % slug)):
            return self.path_exists('_'+slug)
        else:
            return slug

    def delete_repo(self, slug):
        shutil.move(self.path, os.path.join(settings.BRIGITTE_GIT_BASE_PATH,
            '_trash', '%s.git' % self.path_exists(slug)))
        return True

class Commit(BaseCommit):
    @property
    def commit_date(self):
        return datetime.fromtimestamp(float(self.timestamp))

    @property
    def short_long_parents(self):
        return [(parent[:7], parent) for parent in self.parents]

    def get_archive(self):
        cmd1 = 'git --git-dir=%s describe --tags --abbrev=7 %s' % (
            self.repo.path,
            self.id
        )

        try:
            archive_name = self.exec_command_strip(cmd1).replace('-g', '-')
        except:
            archive_name = self.id[:7]

        cmd2 = 'git --git-dir=%s archive --format=zip --prefix=%s-%s/ %s^{tree}' % (
            self.repo.path,
            self.repo.repo.slug,
            archive_name,
            self.id,
        )

        try:
            archive = cStringIO.StringIO()
            archive.write(self.exec_command(cmd2))
            return {
                'filename': archive_name,
                'mime': 'application/zip',
                'data': archive,
            }
        except:
            return None

    def get_tree(self, path, commits=False):
        if not path:
            path = ''
        else:
            if not path[-1] == '/':
                path = path+'/'

        cache_key = '%s:tree:%s:%s:%s' % (self.repo.repo.pk, self.id, path, commits)

        tree_obj = cache.get(cache_key)
        if tree_obj:
            return tree_obj

        cmd = 'git --git-dir=%s ls-tree -l %s %s' % (
            self.repo.path,
            str(self.id),
            path
        )

        try:
            tree_out = []
            raw_tree = self.exec_command_strip(cmd)
            if raw_tree:
                for tree_file in raw_tree.split('\n'):
                    line = TREE_RE.search(tree_file)
                    line_file = line.groupdict()
                    line_file['id'] = line_file['sha']
                    line_file['name'] = line_file['path'].rsplit('/', 1)[-1]

                    if line_file['type'] == 'tree':
                        line_file['path'] += '/'
                    else:
                        if not FILE_RE.match(line_file['name']):
                            if '.' in line_file['name']:
                                line_file['suffix'] = line_file['name'].rsplit('.', 1)[-1]
                                line_file['mime_image'] = FILETYPE_MAP.get(
                                    line_file['suffix'], FILETYPE_MAP['default'])
                            else:
                                line_file['suffix'] = ''
                                line_file['mime_image'] = FILETYPE_MAP['default']
                        else:
                            line_file['suffix'] = ''
                            line_file['mime_image'] = FILETYPE_MAP['default']

                    if commits:
                        line_file['commit'] = self.repo.get_commit(self.id, path=line_file['path'])

                    try:
                        line_file['size'] = float(line_file['size'])
                    except:
                        line_file['size'] = None

                    tree_out.append(line_file)

            tree_out.sort(lambda x, y: cmp(y['type'], x['type']))

            tree_obj = Tree(self.repo, path, tree_out)
            cache.set(cache_key, tree_obj, 2592000)
            return tree_obj
        except:
            raise
            return None

    def get_file(self, path):
        cmd = 'git --git-dir=%s show --exit-code %s:%s' % (
            self.repo.path,
            str(self.id),
            path
        )

        try:
            raw_file = self.exec_command(cmd).decode('utf-8')
            return File(self.repo, path, raw_file, None, None)
        except:
            return None

    @property
    def changed_files(self):
        cmd = 'git --git-dir=%s log -1 --numstat --pretty=format: %s' % (
            self.repo.path,
            str(self.id)
        )

        raw_changed_files = self.exec_command_strip(cmd)
        files = []
        for line in [l.split('\t') for l in raw_changed_files.split('\n') if len(l) > 0]:
            files.append({'file': line[2],
                          'lines_added': line[0],
                          'lines_removed': line[1]})

        return files

    @property
    def commit_diff(self):
        cmd = 'git --git-dir=%s diff-tree -p %s' % (
            self.repo.path,
            str(self.id)
        )
        return self.exec_command(cmd).decode('utf-8')

    def _get_diff_line_numbers(self, diff):
        lines = []
        line1 = 0
        line2 = 0
        hunk_started = False

        for line in diff.splitlines():
            if line.startswith('@@'):
                params = HUNK_RE.match(line).groups()
                lines.append(('..', '..'))
                line1 = int(params[0])
                line2 = int(params[2])
                hunk_started = True
            else:
                if line.startswith('-') and not line.startswith('---'):
                    lines.append((line1, ''))
                    line1 += 1

                elif line.startswith('+') and not line.startswith('+++'):
                    lines.append(('', line2))
                    line2 += 1
                else:
                    if not hunk_started:
                        lines.append(('', ''))
                    else:
                        lines.append((line1, line2))
                        line1 += 1
                        line2 += 1

        return lines

    def get_file_diff(self, path):
        cmd = 'git --git-dir=%s diff --exit-code %s~1 %s -- %s' % (
            self.repo.path,
            self.id,
            self.id,
            path
        )

        try:
            diff = self.exec_command(cmd).decode('utf-8')
            file_diff = {
                'file': path,
                'diff': diff,
                'line_numbers': self._get_diff_line_numbers(diff)
            }
            return file_diff
        except:
            return None

    @property
    def file_diffs(self):
        diff_files = self.changed_files

        for diff_file in diff_files:
            diff_file.update(self.get_file_diff(diff_file['file']))

        return diff_files

class Tag(BaseTag):
    @property
    def last_commit(self):
        if not hasattr(self, '_last_commit'):
            self._last_commit = self.repo.get_commit(
                self.repo.git_repo[self.id].object[1])
        return self._last_commit

class Branch(BaseBranch):
    @property
    def last_commit(self):
        if not hasattr(self, '_last_commit'):
            self._last_commit = self.repo.get_commit(self.id)
        return self._last_commit

class Tree(BaseTree):
    pass

class File(BaseFile):
    pass
