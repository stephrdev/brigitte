# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE
from lxml import etree
import json
from cStringIO import StringIO

class Repo:
    def __init__(self, path):
        self.path = path


    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE)
        output = raw.communicate()[0]
        return output


    def recent_commits(self, sha=None, count=10):
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
                </commit>', sha, '-'+str(count)
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
                commits.append(Commit(c))
        except:
            pass

        return commits


    def commit_files(self, id):
        cmd = ['git',
            '--git-dir=%s' % self.path,
            'diff-tree',
            '-p',
            str(id),
            '--name-status']

        return self.syswrapper(cmd)


    def commit_diff(self, id):
        cmd = ['git',
            '--git-dir=%s' % self.path,
            'diff-tree',
            '-p',
            str(id)]

        return self.syswrapper(cmd)



class Commit:
    def __init__(self, inp):
        self.__dict__.update(**dict([(str(k), v) for k,v in inp.items()]))

    def parents(self):
        return self.parent.split(' ')