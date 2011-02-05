from django.core.management.base import BaseCommand

from brigitte.repositories.utils import update_gitolite

class Command(BaseCommand):
    help = 'Export gitolite config'

    def handle(self, *args, **options):
        update_gitolite()

