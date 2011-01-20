# -*- coding: utf-8 -*-
from lxml import etree
from datetime import datetime

from brigitte.repositories.backends.base import BaseCommit, BaseRepo

class Repo(BaseRepo):
    def get_recent_commits(self, sha=None, count=10):
        if sha == None:
            sha = 'HEAD'

        cmd = ['git',
            '--git-dir=%s' % self.path,
            'log',
            '--no-color',
            '--raw',
            '--pretty=format:\
                <commit>\
                    <timestamp>%ct</timestamp>\
                    <ago>%cr</ago>\
                    <short_msg><![CDATA[%s]]></short_msg>\
                    <committer><![CDATA[%cn]]></committer>\
                    <committer_mail><![CDATA[%ce]]></committer_mail>\
                    <committer_time_iso>%cd</committer_time_iso>\
                    <committer_timestamp>%ct</committer_timestamp>\
                    <author><![CDATA[%an]]></author><author_mail>\
                    <![CDATA[%ae]]></author_mail>\
                    <author_time_iso>%ad</author_time_iso>\
                    <author_timestamp>%at</author_timestamp>\
                    <id>%H</id>\
                    <short_id>%h</short_id>\
                    <parent>%P</parent>\
                    <short_parent>%p</short_parent>\
                    <tree>%T</tree>\
                    <short_tree>%t</short_tree>\
                    <msg><![CDATA[%B]]></msg>\
                </commit>',
            sha,
            '-'+str(count)
        ]

        commits = []
        try:
            outp = '<?xml version="1.0" encoding="UTF-8"?><log>' \
                + self.syswrapper(cmd) + '</log>'

            log = etree.XML(outp)

            for commit in log.iterchildren():
                c = {}
                for field in commit.iterchildren():
                    c[field.tag] = field.text.strip()
                commits.append(Commit(self.path, c))
        except:
            pass

        return commits

    def get_commit(self, sha):
        try:
            return self.get_recent_commits(sha, 1)[0]
        except IndexError:
            pass
        return None

    def get_last_commit(self):
        return self.get_commit(None)

class Commit(BaseCommit):
    def __repr__(self):
        return '<Commit: %s>' % self.id

    @property
    def parents(self):
        return self.parent.split(' ')

    @property
    def short_parents(self):
        return [parent[:7] for parent in self.parents]

    @property
    def both_parents(self):
        return [(parent[:7], parent) for parent in self.parents]

    @property
    def changed_files(self):
        cmd = ['git',
            '--git-dir=%s' % self.path,
            'log',
            '-1',
            '--numstat',
            '--pretty=format:',
            str(self.parents[0]),
            str(self.id),
        ]

        diff_output = self.syswrapper(cmd).strip()
        files = []
        for line in [l for l in diff_output.split('\n') if len(l) > 0]:
            files.append(line.split('\t'))

        return files

    @property
    def diff(self):
        cmd = ['git',
            '--git-dir=%s' % self.path,
            'diff-tree',
            '-p',
            str(self.parents[0]),
            str(self.id)]
        return self.syswrapper(cmd)

    @property
    def commit_date(self):
        return datetime.fromtimestamp(float(self.timestamp))
