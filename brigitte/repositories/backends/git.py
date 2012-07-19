# -*- coding: utf-8 -*-
import re
import os
import operator
import shutil
from datetime import datetime
from django.conf import settings
import cStringIO

from dulwich.diff_tree import tree_changes, tree_changes_for_merge
from dulwich.patch import write_object_diff
from dulwich.repo import Repo as DulwichRepo

from django.core.cache import cache

from brigitte.repositories.backends.base import BaseRepo, BaseCommit
from brigitte.repositories.backends.base import BaseTag, BaseBranch
from brigitte.repositories.backends.base import BaseFile, BaseTree


FILETYPE_MAP = getattr(settings, 'FILETYPE_MAP', {})
AUTHOR_EMAIL_RE=re.compile('(.*) <(.*)>')
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
            in sorted(self.get_refs('tags'),
                key=operator.itemgetter(2), reverse=True)
        ]

    @property
    def branches(self):
        return [Branch(self, branch, sha)
            for branch, sha, time
            in sorted(self.get_refs('heads'),
                key=operator.itemgetter(2), reverse=True)
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
        cache_key = '%s:commit:%s:%s' % (self.repo.pk, sha, path or 'no-path')

        commit = None

        if sha:
            commit = cache.get(cache_key)

        if not commit:
            try:
                commit = self._get_commit_list(
                    sha=sha, count=1, skip=0, path=path)[0]
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

    def trash_path_exists(self, slug):
        if os.path.exists(os.path.join(
            settings.BRIGITTE_GIT_BASE_PATH, '_trash', '%s.git' % slug)):
            return self.path_exists('_'+slug)
        else:
            return slug

    def delete_repo(self, slug):
        shutil.move(self.path, os.path.join(settings.BRIGITTE_GIT_BASE_PATH,
            '_trash', '%s.git' % self.trash_path_exists(slug)))
        return True

class Commit(BaseCommit):
    @property
    def commit_date(self):
        return datetime.fromtimestamp(float(self.timestamp))

    @property
    def short_long_parents(self):
        return [(parent[:7], parent) for parent in self.parents]

    def get_tree(self, path, commits=False):
        if not path:
            path = ''
        else:
            if not path[-1] == '/':
                path = path+'/'

        cache_key = '%s:tree:%s:%s:%s' % (
            self.repo.repo.pk, self.id, path, commits)

        tree_obj = cache.get(cache_key)

        if not tree_obj:
            tree = self.repo.git_repo.tree(self.repo.git_repo.tree(
                self.tree).lookup_path(self.repo.git_repo.tree, path)[1])

            tree_output = []
            for entry in tree.iteritems():
                entry_object = self.repo.git_repo.get_object(entry.sha)
                parsed_entry = {
                    'rights': entry.mode,
                    'type': entry_object.type_name,
                    'id': entry.sha,
                    'sha': entry.sha,
                    'path': entry.in_path(path).path,
                    'name': entry.path
                }

                if entry_object.type_name == 'tree':
                    parsed_entry['size'] = None
                    parsed_entry['path'] += '/'
                else:
                    parsed_entry['size'] = float(entry_object.raw_length())
                    # We skip dot-files at the moment.
                    if '.' in parsed_entry['name'] and parsed_entry['name'][0] != '.':
                        parsed_entry['suffix'] = parsed_entry['name'].rsplit('.', 1)[-1]
                        parsed_entry['mime_image'] = FILETYPE_MAP.get(
                            parsed_entry['suffix'], FILETYPE_MAP['default'])
                    else:
                        parsed_entry['suffix'] = ''
                        parsed_entry['mime_image'] = FILETYPE_MAP['default']

                if commits:
                    # WOAAAA THIS IS SLOW!
                    parsed_entry['commit'] = self.repo.get_commit(
                        self.id, path=parsed_entry['path'].rstrip('/'))

                tree_output.append(parsed_entry)

            tree_output.sort(lambda x, y: cmp(y['type'], x['type']))

            tree_obj = Tree(self.repo, path, tree_output)
            cache.set(cache_key, tree_obj, 2592000)

        return tree_obj

    def get_file(self, path):
        cache_key = '%s:blob:%s:%s' % (self.repo.repo.pk, self.id, path)

        blob = cache.get(cache_key)

        if not blob:
            blob = self.repo.git_repo.get_blob(self.repo.git_repo.tree(
                self.tree).lookup_path(self.repo.git_repo.tree, path)[1])
            cache.set(cache_key, blob, 2592000)

        return File(self.repo, path, blob.data.decode('utf-8'), None, None)

    def get_tree_changes(self, as_dict=False):
        cache_key = '%s:tree_changes:%s' % (self.repo.repo.pk, self.id)

        tree_changes_cache = cache.get(cache_key)

        if tree_changes_cache:
            self._tree_changes, self._tree_changes_dict = tree_changes_cache
        else:
            if not self.parents:
                changes_func = tree_changes
                parent = None
            elif len(self.parents) == 1:
                changes_func = tree_changes
                parent = self.repo.git_repo[self.parents[0]].tree
            else:
                changes_func = tree_changes_for_merge
                parent = [self.repo.git_repo[p].tree for p in self.parents]

            self._tree_changes = list(changes_func(
                self.repo.git_repo, parent, self.tree))
            self._tree_changes_dict = dict([(c.new.path, c)
                for c in self._tree_changes])

            cache.set(cache_key,
                (self._tree_changes, self._tree_changes_dict), 2592000)

        if as_dict:
            return self._tree_changes_dict
        else:
            return self._tree_changes

    @property
    def changed_files(self):
        cache_key = '%s:changed_files:%s' % (self.repo.repo.pk, self.id)

        files = cache.get(cache_key)

        if not files:
            files = []
            for change in self.get_tree_changes():
                diff = cStringIO.StringIO()
                write_object_diff(diff, self.repo.git_repo,
                    change.old, change.new)
                diff = diff.getvalue()
                lines_added, lines_removed = self._get_diff_line_numbers(diff, count=True)
                files.append({
                    'file': change.new.path,
                    'lines_added': lines_added,
                    'lines_removed': lines_removed,
                    'change_type': change.type,
                })
            cache.set(cache_key, files, 2592000)

        return files

    def _get_diff_line_numbers(self, diff, count=False):
        lines = []
        line1 = 0
        line2 = 0
        lines_added = 0
        lines_removed = 0
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
                    lines_removed += 1
                elif line.startswith('+') and not line.startswith('+++'):
                    lines.append(('', line2))
                    line2 += 1
                    lines_added += 1
                else:
                    if not hunk_started:
                        lines.append(('', ''))
                    else:
                        lines.append((line1, line2))
                        line1 += 1
                        line2 += 1

        if count:
            return (lines_added, lines_removed)
        else:
            return lines

    def get_file_diff(self, path):
        cache_key = '%s:file_diff:%s:%s' % (self.repo.repo.pk, self.id, path)

        file_diff = cache.get(cache_key)

        if not file_diff:
            files = self.get_tree_changes(True)
            diff = cStringIO.StringIO()
            write_object_diff(diff, self.repo.git_repo,
                files[path].old, files[path].new)
            diff = diff.getvalue().decode('utf-8')

            file_diff = {
                'file': path,
                'diff': diff,
                'line_numbers': self._get_diff_line_numbers(diff)
            }
            cache.set(cache_key, file_diff, 2592000)

        return file_diff

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
