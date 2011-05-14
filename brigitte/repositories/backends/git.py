# -*- coding: utf-8 -*-
import re
import os
import shutil
from datetime import datetime
from django.conf import settings
import cStringIO
from brigitte.repositories.backends.base import BaseRepo, BaseCommit
from brigitte.repositories.backends.base import BaseTag, BaseBranch
from brigitte.repositories.backends.base import BaseFile, BaseTree

try:
    from lxml import etree

    def parse_log_xml(raw_log):
        log = etree.XML(raw_log)
        for commit in log.iterchildren():
            c = {}
            for field in commit.iterchildren():
                if field.text:
                    c[field.tag] = field.text.strip()
            yield c

    def parse_single_xml(raw_log):
        log = etree.XML(raw_log)
        c = {}
        for field in log.iterchildren():
            if field.text:
                c[field.tag] = field.text.strip()
        return c

except ImportError:
    import xml.etree.ElementTree as ET

    def parse_log_xml(raw_log):
        log = ET.fromstring(raw_log)
        for commit in log.findall('commit'):
            c = {}
            for key in commit:
                if key.text:
                    c[key.tag] = key.text
            yield c

    def parse_single_xml(raw_log):
        log = ET.fromstring(raw_log)
        c = {}
        for elem in list(log):
            c[elem.tag] = elem.text
        return c


FILETYPE_MAP = getattr(settings, 'FILETYPE_MAP', {})

BRANCHES_RE = re.compile("^(?P<type>\s|\*) (?P<name>.+)$", re.MULTILINE)

TREE_RE = re.compile(
    "(?P<rights>\d*)\s(?P<type>[a-z]*)"
    "\s(?P<sha>\w*)\s*(?P<size>[0-9 -]*)\s*(?P<path>.+)")

FILE_RE = re.compile("\.\w+")
HUNK_RE = re.compile(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@')

class Repo(BaseRepo):

    @property
    def tags(self):
        cmd = 'git --git-dir=%s show-ref --tags' % self.path
        tags = self.exec_command(cmd).split('\n')
        tags.reverse()

        tag_list = []
        for sha, tag in [tag.split(' ') for tag in tags if len(tag) > 0]:
            tag = tag.split('/', 2)[-1]
            tag_list.append(Tag(self, tag, sha))

        return tag_list

    @property
    def branches(self):
        cmd = 'git --git-dir=%s show-ref --heads' % self.path

        branches = self.exec_command(cmd).split('\n')

        branch_list = []
        for sha, branch in [branch.split(' ') for branch in branches if len(branch) > 0]:
            branch = branch.split('/', 2)[-1]
            branch_list.append(
                Branch(self, branch, sha, False))

        return branch_list

    def _get_commit_list(self, sha=None, count=10, skip=0, head=None, path=None):
        if sha == None:
            sha = head if head else 'HEAD'

        cmd = ['git',
            '--git-dir=%s' % self.path,
            'log',
            '--no-color',
            '--raw',
            '--pretty=format:\
                <commit>\
                    <id>%H</id>\
                    <tree>%T</tree>\
                    <parent>%P</parent>\
                    <short_message><![CDATA[%s]]></short_message>\
                    <message><![CDATA[%B]]></message>\
                    <author><![CDATA[%an]]></author>\
                    <author_email><![CDATA[%ae]]></author_email>\
                    <committer><![CDATA[%cn]]></committer>\
                    <committer_email><![CDATA[%ce]]></committer_email>\
                    <timestamp>%ct</timestamp>\
                </commit>',
            '--skip=' + str(skip),
            '-' + str(count),
            sha,
        ]

        if path:
            cmd.append('--')
            cmd.append(path)


        commits = []
        try:
            raw_log = '<?xml version="1.0" encoding="UTF-8"?>\
                <log>%s</log>' % self.exec_command(cmd)

            for commit in parse_log_xml(raw_log):
                commits.append(Commit(self, commit))
        except:
            pass

        return commits

    def get_commits(self, count=10, skip=0, head=None, path=None):
        return self._get_commit_list(
            sha=None, count=count, skip=skip, head=head, path=path)

    def get_commit(self, sha, path=None):
        try:
            return self._get_commit_list(sha=sha, count=1, skip=0, path=path)[0]
        except IndexError:
            pass
        return None

    @property
    def last_commit(self):
        return self.get_commit(None)

    def init_repo(self):
        cmd = 'git init -q --shared=0770 --bare %s --template=%s/%s' % (self.path, settings.PROJECT_ROOT, 'repo_templates/git/')
        self.exec_command(cmd)
        return True

    def path_exists(self, slug):
        if os.path.exists(os.path.join(settings.BRIGITTE_GIT_BASE_PATH, '_trash', '%s.git' % slug)):
            return self.path_exists('_'+slug)
        else:
            return slug

    def delete_repo(self, slug):
        shutil.move(self.path, os.path.join(settings.BRIGITTE_GIT_BASE_PATH, '_trash', '%s.git' % self.path_exists(slug)))
        return True

class Commit(BaseCommit):
    @property
    def commit_date(self):
        return datetime.fromtimestamp(float(self.timestamp))

    @property
    def parents(self):
        return self.parent.split(' ')

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

    def get_tree(self, path):
        if not path:
            path = ''
        else:
            if not path[-1] == '/':
                path = path+'/'

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

                    line_file['commit'] = self.repo.get_commit(self.id, path=line_file['path'])

                    try:
                        line_file['size'] = float(line_file['size'])
                    except:
                        line_file['size'] = None

                    tree_out.append(line_file)

            tree_out.sort(lambda x, y: cmp(y['type'], x['type']))

            return Tree(self.repo, path, tree_out)
        except:
            return None

    def get_file(self, path):
        cmd = 'git --git-dir=%s show --exit-code %s:%s' % (
            self.repo.path,
            str(self.id),
            path
        )

        try:
            raw_file = self.exec_command(cmd)
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
        return self.exec_command(cmd)

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
            diff = self.exec_command(cmd)
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
            try:
                self._last_commit = self.repo.get_commit(self.id)
            except:
                self._last_commit = None
        return self._last_commit

class Branch(BaseBranch):
    @property
    def last_commit(self):
        if not hasattr(self, '_last_commit'):
            try:
                self._last_commit = self.repo.get_commit(self.id)
            except:
                self._last_commit = None
        return self._last_commit

class Tree(BaseTree):
    pass

class File(BaseFile):
    pass

