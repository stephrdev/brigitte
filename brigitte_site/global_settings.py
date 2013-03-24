# -*- coding: utf-8 -*-
import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
from django.conf.global_settings import MIDDLEWARE_CLASSES

# project name and root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

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
LANGUAGE_CODE = 'en'
USE_I18N = True

# available languages
gettext_noop = lambda s: s
LANGUAGES = (
    ('en', gettext_noop('English')),
)

SITE_ID = 1

STATIC_URL = '/static_media/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'deployed_static_media')

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static_media'),
)

ROOT_URLCONF = '%s.urls' % PROJECT_NAME

AUTHENTICATION_BACKENDS = (
    'userprofiles.auth_backends.EmailOrUsernameModelBackend',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'floppyforms',
    'south',
    'userprofiles',
    'userprofiles.contrib.accountverification',
    'userprofiles.contrib.emailverification',
    'userprofiles.contrib.profiles',
    'brigitte.accounts',
    'brigitte.repositories',
    'brigitte.utils',
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

LOGIN_REDIRECT_URL = '/accounts/profile/'

FILETYPE_MAP = {
    'default': 'file.png',
    '7z': '7z.png',
    'ai': 'ai.png',
    'asc': 'asc.png',
    'bin': 'bin.png',
    'bz2': 'bz2.png',
    'c': 'c.png',
    'cfc': 'cfc.png',
    'cfm': 'cfm.png',
    'chm': 'chm.png',
    'class': 'class.png',
    'conf': 'conf.png',
    'cpp': 'cpp.png',
    'cs': 'cs.png',
    'css': 'css.png',
    'csv': 'csv.png',
    'deb': 'deb.png',
    'divx': 'divx.png',
    'doc': 'doc.png',
    'dot': 'dot.png',
    'eml': 'eml.png',
    'enc': 'enc.png',
    'gif': 'gif.png',
    'gz': 'gz.png',
    'hlp': 'hlp.png',
    'htm': 'htm.png',
    'html': 'html.png',
    'iso': 'iso.png',
    'jar': 'jar.png',
    'java': 'java.png',
    'jpeg': 'jpeg.png',
    'jpg': 'jpg.png',
    'js': 'js.png',
    'lua': 'lua.png',
    'm': 'm.png',
    'mm': 'mm.png',
    'mov': 'mov.png',
    'mp3': 'mp3.png',
    'mpg': 'mpg.png',
    'odc': 'odc.png',
    'odf': 'odf.png',
    'odg': 'odg.png',
    'odi': 'odi.png',
    'odp': 'odp.png',
    'ods': 'ods.png',
    'odt': 'odt.png',
    'ogg': 'ogg.png',
    'pdf': 'pdf.png',
    'pgp': 'pgp.png',
    'php': 'php.png',
    'pl': 'pl.png',
    'png': 'png.png',
    'ppt': 'ppt.png',
    'ps': 'ps.png',
    'py': 'py.png',
    'ram': 'ram.png',
    'rar': 'rar.png',
    'rb': 'rb.png',
    'rm': 'rm.png',
    'rpm': 'rpm.png',
    'rtf': 'rtf.png',
    'sig': 'sig.png',
    'sql': 'sql.png',
    'swf': 'swf.png',
    'sxc': 'sxc.png',
    'sxd': 'sxd.png',
    'sxi': 'sxi.png',
    'sxw': 'sxw.png',
    'tar': 'tar.png',
    'tex': 'tex.png',
    'tgz': 'tgz.png',
    'txt': 'txt.png',
    'vcf': 'vcf.png',
    'vsd': 'vsd.png',
    'wav': 'wav.png',
    'wma': 'wma.png',
    'wmv': 'wmv.png',
    'xls': 'xls.png',
    'xml': 'xml.png',
    'xpi': 'xpi.png',
    'xvid': 'xvid.png',
    'zip': 'zip.png'
}

USERPROFILES_CHECK_UNIQUE_EMAIL = True
USERPROFILES_DOUBLE_CHECK_EMAIL = True
USERPROFILES_DOUBLE_CHECK_PASSWORD = True
USERPROFILES_REGISTRATION_FULLNAME = True
USERPROFILES_USE_ACCOUNT_VERIFICATION = True
USERPROFILES_USE_EMAIL_VERIFICATION = True
USERPROFILES_USE_PROFILE = True
USERPROFILES_INLINE_PROFILE_ADMIN = True
USERPROFILES_REGISTRATION_FORM = 'brigitte.accounts.forms.ProfileRegistrationForm'
