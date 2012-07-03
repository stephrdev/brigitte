from global_settings import *

DEBUG = TEMPLATE_DEBUG = THUMBNAIL_DEBUG = True

# database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'local_database.db'
    }
}

ADMINS = (
    ('steph', 'steph@rdev.info'),
)
MANAGERS = ADMINS

# default mail settings
DEFAULT_FROM_EMAIL = 'steph@rdev.info'
SERVER_EMAIL = 'steph@rdev.info'

EMAIL_HOST = 'localhost'
EMAIL_PORT = 2525

# cache settings
#CACHE_BACKEND = 'locmem:///'

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
    },
}

BROKER_BACKEND = 'redis'
BROKER_HOST = 'localhost'
BROKER_PORT = 6379
BROKER_VHOST = '1'

# INSTALLED_APPS += (
#     'debug_toolbar',
# )
# MIDDLEWARE_CLASSES += (
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# )
# INTERNAL_IPS = ('127.0.0.1',)
# 
# DEBUG_TOOLBAR_CONFIG = {
#     'INTERCEPT_REDIRECTS': False,
# }

BRIGITTE_GIT_BASE_PATH = '/Users/steph/Projects/brigitte_repos/'
BRIGITTE_GIT_ADMIN_PATH = '/Users/steph/Projects/brigitte_admin/'
