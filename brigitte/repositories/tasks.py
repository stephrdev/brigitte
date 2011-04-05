from celery.task import Task
from celery.registry import tasks
from datetime import datetime
from brigitte.repositories.models import RepositoryUpdate

class UpdateGitoliteTask(Task):
    default_retry_delay = 10
    max_retries = 3

    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)

        try:
            logger.info('updating gitolite..')
            if RepositoryUpdate.objects.filter(is_exported=False).count() > 0:
                from brigitte.repositories.utils import update_gitolite
                update_gitolite()
                RepositoryUpdate.objects.filter(is_exported=False).update(
                    is_exported=True,
                    exported=datetime.now()
                )
                logger.info('updated!')
            else:
                logger.info('no update needed!')
            return True
        except Exception, exc:
            logger.error('failed: %s' % exc)
            self.retry([], kwargs, exc=exc)
            return False

tasks.register(UpdateGitoliteTask)
