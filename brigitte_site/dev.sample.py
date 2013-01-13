from global_settings import *

DEBUG = TEMPLATE_DEBUG = THUMBNAIL_DEBUG = True

SECRET_KEY = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'local_database.db'
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        'OPTIONS': {
            'DB': 0,
        },
    },
}

ADMINS = (
    ('root', 'root@localhost'),
)
MANAGERS = ADMINS

STATIC_ROOT = os.path.join(PROJECT_ROOT, '..', '..', 'static_media')

DEFAULT_FROM_EMAIL = 'root@localhost'
SERVER_EMAIL = 'root@localhost'

BRIGITTE_GIT_BASE_PATH = os.path.join(PROJECT_ROOT, '..', '..', 'repositories')
BRIGITTE_SSH_KEY_PATH = os.path.join(PROJECT_ROOT, '..', '..', 'sshserver_key')
BRIGITTE_SSH_PORT = 2222
