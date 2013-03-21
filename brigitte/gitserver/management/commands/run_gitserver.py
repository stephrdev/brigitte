# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand

from twisted.conch.interfaces import ISession
from twisted.internet import reactor
from twisted.python import components

from brigitte.gitserver.server import GitSession, GitConchUser, GitServer


class Command(BaseCommand):
    help = 'Starts the GitServer for brigitte.'

    def handle(self, *args, **options):
        components.registerAdapter(GitSession, GitConchUser, ISession)
        reactor.listenTCP(settings.BRIGITTE_SSH_PORT,
            GitServer(settings.BRIGITTE_SSH_KEY_PATH))
        reactor.run()
