import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
from django.conf.global_settings import MIDDLEWARE_CLASSES

# project name and root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

# secret string for session encryption
try:
    SECRET_KEY
except NameError:
    SECRET_FILE = os.path.join(PROJECT_ROOT, 'secret.txt')
    try:
        SECRET_KEY = open(SECRET_FILE).read().strip()
    except IOError:
        try:
            from random import choice
            SECRET_KEY = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            secret = file(SECRET_FILE, 'w')
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception('Please create a %s file with random characters to generate your secret key!' % SECRET_FILE)

# disable debug by default
DEBUG = TEMPLATE_DEBUG = False

# 500 mails should go to:
ADMINS = (
    ('admin', 'admin@example.com'),
)
MANAGERS = ADMINS

# default mail settings
DEFAULT_FROM_EMAIL = 'webmaster@example.com'
SERVER_EMAIL = 'webmaster@example.com'
EMAIL_SUBJECT_PREFIX = '[%s] ' % PROJECT_NAME

# i18n/i10n stuff
TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de'
USE_I18N = True

# available languages
gettext_noop = lambda s: s
LANGUAGES = (
    ('de', gettext_noop('German')),
    ('en', gettext_noop('English')),
)

SITE_ID = 1

# site media and static media
ADMIN_MEDIA_PREFIX = '/admin_media/'

STATIC_URL = '/static_media/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static_media')

STATICFILES_DIRS = (
	os.path.join(PROJECT_ROOT, 'static_media'),
)

ROOT_URLCONF = '%s.urls' % PROJECT_NAME

AUTHENTICATION_BACKENDS = (
    'brigitte.accounts.auth_backends.EmailOrUsernameModelBackend',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'south',

    'brigitte.accounts',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# add some context processors
TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
)

MIDDLEWARE_CLASSES += (
    'django.contrib.messages.middleware.MessageMiddleware',
)

# where to look for templates?
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

AUTH_PROFILE_MODULE = 'accounts.Profile'

LOGIN_REDIRECT_URL = '/accounts/'

ACCOUNT_ACTIVATION_DAYS = 7

