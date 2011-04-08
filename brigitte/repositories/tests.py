from contextlib import contextmanager

from django.contrib.auth.models import User
from django.utils import unittest

from brigitte.repositories.models import Repository
from brigitte.repositories.backends.git import Repo as GitRepo


class PathNamesTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testmaster', first_name='Test', last_name='Master',
            email='test@master.com', password=''
        )
        self.repo = Repository.objects.create(
            user=self.user, slug='hr_r_whtspcs',
            title='Whitespace Test Repository',
            description='None available'
        )

    def test_whitespace(self):
        import brigitte.repositories.models
        brigitte.repositories.models.BRIGITTE_GIT_BASE_PATH = 'brigitte repos'
        gr = GitRepo(self.repo)
        gr.init_repo()

