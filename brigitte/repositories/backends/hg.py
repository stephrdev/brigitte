# -*- coding: utf-8 -*-
import re
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

FILETYPE_MAP = getattr(settings, 'FILETYPE_MAP', {})

BRANCHES_RE = re.compile("^([\w\.]+)\s+(\d+):(\w+).$",re.MULTILINE)

TAGS_RE = re.compile("^([\w\.]+)\s+(\d+):(\w+).$",re.MULTILINE)

TREE_RE = re.compile(
    "(?P<rights>\d*)\s(?P<type>[a-z]*)"\
    "\s(?P<sha>\w*)\s*(?P<size>[0-9 -]*)\s*(?P<path>.+)")

FILE_RE = re.compile("\.\w+")
HUNK_RE = re.compile(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@')

class Repo(BaseRepo):
    @property
    def tags(self):

        cmd = 'hg --cwd "%s" tags' % self.path
        tags = self.exec_command(cmd)
        tags = TAGS_RE.findall(tags)

        tag_list = []
        for tag, ignore, sha in tags:
            tag_list.append(Tag(self, tag, sha))

        return tag_list

    @property
    def branches(self):
        cmd = 'hg --cwd "%s" branches' % self.path
        branches = self.exec_command(cmd)
        branches = BRANCHES_RE.findall(branches)

        branch_list = []
        for branch, ignore, sha in branches:
            branch_list.append(Branch(self, branch, sha, False))

        return branch_list

    def _get_commit_list(self, sha=None, count=10, skip=0, head=None):
        if sha == None:
            if head and head <> 'default' and head <> 'tip':
                raise NotImplementedError
            sha = 'tip'

        skip += 1
        count += skip - 1

        if count > 1:
            sha = '-%s:-%s' % (str(skip), str(count))

        cmd = ['hg',
            '--cwd',
            self.path,
            'log',

            '--template="\
                <commit>\
                    <id>{node}</id>\
                    <tree>{node}</tree>\
                    <short_message><![CDATA[{desc|firstline}]]></short_message>\
                    <message><![CDATA[{desc}]]></message>\
                    <author><![CDATA[{author|person}]]></author>\
                    <author_email><![CDATA[{author|email}]]></author_email>\
                    <committer><![CDATA[{author|person}]]></committer>\
                    <committer_email><![CDATA[{author|email}]]></committer_email>\
                    <timestamp>{date}</timestamp>\
                </commit>"',
            '-r',
            sha,
        ]

        commits = []
        try:
            raw_log = '<?xml version="1.0" encoding="UTF-8"?>\
                <log>%s</log>' % self.exec_command(cmd)

            for commit in parse_log_xml(raw_log):
                commits.append(Commit(self, commit))
        except:
            raise

        return commits

    def get_commits(self, count=10, skip=0, head=None):
        return self._get_commit_list(
            sha=None, count=count, skip=skip, head=head)

    def get_commit(self, sha):
        try:
            return self._get_commit_list(sha=sha, count=1, skip=0)[0]
        except IndexError:
            pass
        return None

    @property
    def last_commit(self):
        return self.get_commit(None)

    def init_repo(self):
        cmd = 'hg init "%s"' % (self.path)
        self.exec_command(cmd)
        return True

class Commit(BaseCommit):
    @property
    def commit_date(self):
        return datetime.fromtimestamp(float(self.timestamp.split('.', 1)[0]))

    @property
    def parents(self):
        return self.parent.split(' ')

    @property
    def short_long_parents(self):
        return [(parent[:7], parent) for parent in self.parents]

    def get_archive(self):
        #cmd1 = 'hg --git-dir=%s describe --tags --abbrev=7 %s' % (
        #    self.repo.path,
        #    self.id
        #)

        #try:
        #    archive_name = self.exec_command_strip(cmd1).replace('-g', '-')
        #except:

        archive_name = self.id[:7]

        cmd2 = 'hg --cwd "%s" archive -t zip -r %s -' % (
            self.repo.path,
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

        cmd = 'git --git-dir="%s" ls-tree -l %s "%s"' % (
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

                    tree_out.append(line_file)

            tree_out.sort(lambda x, y: cmp(y['type'], x['type']))

            return Tree(self.repo, path, tree_out)
        except:
            return None

    def get_file(self, path):
        cmd = 'git --git-dir="%s" show --exit-code %s:"%s"' % (
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
        cmd = 'hg --cwd "%s" status --change %s' % (
            self.repo.path,
            str(self.id)
        )

        raw_changed_files = self.exec_command_strip(cmd)
        files = []
        for line in [l.split(' ') for l in raw_changed_files.split('\n') if len(l) > 0]:
            files.append({'file': line[1],
                          'lines_added': 1 if line[0] == 'A' else 1 if line[0] == 'M' else 0,
                          'lines_removed':  1 if line[0] == 'R' else 1 if line[0] == 'M' else 0})

        return files

    @property
    def commit_diff(self):
        cmd = 'hg --cwd "%s" diff -g -r %s' % (
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
        cmd = 'hg --cwd "%s" diff -g -c %s "%s"' % (
            self.repo.path,
            self.id,
            path
        )
        print cmd
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

