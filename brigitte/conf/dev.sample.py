from conf.global_settings import *

DEBUG = TEMPLATE_DEBUG = THUMBNAIL_DEBUG = True

# database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'local_database.db'
    }
}

ADMINS = (
    ('root', 'root@localhost'),
)
MANAGERS = ADMINS

# default mail settings
DEFAULT_FROM_EMAIL = 'root@localhost'
SERVER_EMAIL = 'root@localhost'

BRIGITTE_GIT_BASE_PATH = 'brigitte_repos'

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        'OPTIONS': {
            'DB': 0,
        },
    },
}

BROKER_BACKEND = 'redis'
BROKER_HOST = '127.0.0.1'
BROKER_PORT = 6379
BROKER_VHOST = '1'

