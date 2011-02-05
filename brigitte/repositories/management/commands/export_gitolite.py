from django.core.management.base import BaseCommand
from django.conf import settings

from brigitte.repositories.gitolite import generate_gitolite_conf, export_public_keys

import os

BRIGITTE_GIT_ADMIN_PATH = getattr(settings,
                                  'BRIGITTE_GIT_ADMIN_PATH',
                                  'gitolite-admin')

class Command(BaseCommand):
    help = 'Export gitolite config'

    def handle(self, *args, **options):

        generate_gitolite_conf(os.path.join(BRIGITTE_GIT_ADMIN_PATH,
                                            'conf/gitolite.conf'))

        export_public_keys(os.path.join(BRIGITTE_GIT_ADMIN_PATH, 'keydir'))

