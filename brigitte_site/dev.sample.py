from global_settings import *

DEBUG = TEMPLATE_DEBUG = THUMBNAIL_DEBUG = True

# database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'local_database.db'
    }
}

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql_psycopg2',
#        'NAME': '',
#        'USER': '',
#        'PASSWORD': '',
#        'OPTIONS': {
#            'autocommit': True,
#        }
#    }
#}


ADMINS = (
    ('root', 'root@localhost'),
)
MANAGERS = ADMINS

# default mail settings
DEFAULT_FROM_EMAIL = 'root@localhost'
SERVER_EMAIL = 'root@localhost'

BRIGITTE_GIT_BASE_PATH = os.path.join(PROJECT_ROOT, '..', 'brigitte_repos')
BRIGITTE_SSH_PORT = 2222
BRIGITTE_SSH_KEY_PATH = os.path.join(PROJECT_ROOT, 'sshserver_key')

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        'OPTIONS': {
            'DB': 0,
        },
    },
}
