from django.core.management.base import BaseCommand

from brigitte.repositories.models import Repository

class Command(BaseCommand):
    help = 'Export gitolite config'

    def handle(self, *args, **options):
        debug = False
        def generate_access_rule(repo_user, key):
            if repo_user.can_write and key.can_write:
                return 'RW+'
            elif repo_user.can_read and key.can_read:
                return 'R'

        for repo in Repository.objects.all():
            if debug:
                print '# repository: %s' % repo
            print 'repo\t%s' % repo.short_path
            for user in repo.repositoryuser_set.all():
                if debug:
                    print '\t# user: %s' % user
                    print '\t# read: %s, write: %s' % (user.can_read, user.can_write)
                for key in user.user.sshpublickey_set.all():
                    if debug:
                        print '\t# key - read: %s, write: %s' % (key.can_read, key.can_write)
                    print '\t%s\t= key-%s' % (generate_access_rule(user, key), key.pk)
