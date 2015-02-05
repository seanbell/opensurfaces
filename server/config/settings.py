# Django settings

# import settings from settings_local.py
import os
import datetime
from settings_local import *

MANAGERS = ADMINS
TEMPLATE_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# allowed languages for an account
ACCOUNT_LANGUAGES = (('en-us', 'English'),)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Wrap each HTTP request in a database transaction
ATOMIC_REQUESTS = True
AUTOCOMMIT = True

# Directory containing website code
SRC_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))

# Absolute filesystem path to the directory that will hold user-uploaded files.
# (note that OpenSurfaces doesn't use this.  Uploaded files are saved
# elsewhere; see DEFAULT_FILE_STORAGE in settings.py).
MEDIA_ROOT = os.path.join(DATA_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# temporary hack-fix for django-admin-tools
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
STATIC_ROOT = os.path.join(DATA_DIR, 'static')

# Default file permissions
FILE_UPLOAD_PERMISSIONS = 0644

# URL prefix for static files.
# NOTE: In a few places, this is hard-coded.  So you should search through the
# entire codebase for accidental uses of '/static/' if you ever want to change
# this.
STATIC_URL = '/static/'

# HTTPS / SSL
#if ENABLE_SSL:
    #CSRF_COOKIE_SECURE = True
    #SESSION_COOKIE_SECURE = True


# file storage for new experiments -- store either on S3 or on the local
# filesystem.
if S3_ENABLE:
    if S3_ENABLE_WRITE:
        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    else:
        DEFAULT_FILE_STORAGE = 'common.backends.ReadOnlyS3BotoStorage'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# file storage for OpenSurfaces experiments
if OPENSURFACES_USE_REMOTE_DATA:
    OPENSURFACES_FILE_STORAGE = 'common.backends.OpenSurfacesStorage'
else:
    OPENSURFACES_FILE_STORAGE = DEFAULT_FILE_STORAGE


AWS_QUERYSTRING_AUTH = False  # don't include authentication in URL
AWS_S3_SECURE_URLS = ENABLE_SSL  # use http
AWS_HEADERS = {
    'Expires': '1 Jan %s 00:00:00 GMT' % (datetime.datetime.today().year + 1),
    'Cache-Control': 'max-age=2592000, public',
}

#STATICFILES_STORAGE = 'common.backends.StaticQueuedS3BotoStorage'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SRC_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
    #'django.template.loaders.eggs.Loader',
)

# Cache in production
if not DEBUG:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', TEMPLATE_LOADERS),
    )


MIDDLEWARE_CLASSES = tuple(filter(None, [
    # default site-wide caching
    'django.middleware.cache.UpdateCacheMiddleware' if CACHE_MIDDLEWARE_ENABLE else None,

    # gzip compression
    'django.middleware.gzip.GZipMiddleware',

    # django-debug-toolbar
    'debug_toolbar.middleware.DebugToolbarMiddleware' if DEBUG and DEBUG_TOOLBAR else None,

    # profilers (alternative to django-debug-toolbar)
    'common.middleware.HotshotProfileMiddleware' if DEBUG and not DEBUG_TOOLBAR else None,
    #'common.middleware.CProfileProfilerMiddleware' if DEBUG and not DEBUG_TOOLBAR else None,

    # default middleware:
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # for admin docs:
    'django.middleware.doc.XViewMiddleware',

    # accounts
    'account.middleware.LocaleMiddleware' if USE_I18N else None,
    'account.middleware.TimezoneMiddleware' if USE_TZ else None,

    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # default site-wide caching
    'django.middleware.cache.FetchFromCacheMiddleware' if CACHE_MIDDLEWARE_ENABLE else None,
]))

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'cache_panel.panel.CacheDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

ROOT_URLCONF = 'config.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATE_DIRS = (
    # Note: Django source files are here:
    # /usr/local/lib/python2.7/dist-packages/django
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SRC_DIR, 'templates'),
)

# django-endless-pagination
ENDLESS_PAGINATION_PER_PAGE = 48
ENDLESS_PAGINATION_LOADING = (
    "<img src='%simg/ajax-loader.gif' alt='loading...'/>" % STATIC_URL)
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
    'common.context_processors.debug',
    #'account.context_processors.account',
)

# cache with memcached
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
CACHE_MIDDLEWARE_SECONDS = 21600
if ENABLE_CACHING:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
            'LOCATION': '127.0.0.1:11211',
        },
        'persistent': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'db-cache',
            'TIMEOUT': None,
        }
    }

INSTALLED_APPS = tuple(filter(None, [
    # django-admin-tools
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    # django libraries
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    # green unicorn wsgi server
    'gunicorn',
    # db migrations
    'south',
    # storage
    'storages',
    'queued_storage',
    # handy extensions
    'django_extensions',
    # user accounts
    'account',
    'django_forms_bootstrap',
    # content
    'imagekit',
    'compressor',
    'endless_pagination',
    'cacheback',
    'captcha',
    # debug tools
    'debug_toolbar' if DEBUG and DEBUG_TOOLBAR else None,
    'cache_panel' if DEBUG and DEBUG_TOOLBAR else None,
    'memcache_status',
    # my apps
    'common',
    'home',
    'accounts',
    'analytics',
    'licenses',
    'poly',
    'mturk',
    'photos',
    'shapes',
    'bsdfs',
    'normals',
    'intrinsic',
]))

# A sample logging configuration. The only tangible logging performed by this
# configuration is to send an email to the site admins on every HTTP 500 error
# when DEBUG=False.  Emails are rate-limited, so only the first message within
# each 1 second window is reported via email.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        #'rate_limit': {
        #    '()': 'common.log.RateLimitFilter',
        #    'rate': 1,
        #}
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# allow email login
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'account.auth_backends.EmailAuthenticationBackend',
)

# To indicate that this model is the user profile model for a given site, fill
# in the setting AUTH_PROFILE_MODULE with a string consisting of the following
# items, separated by a dot
AUTH_PROFILE_MODULE = 'accounts.UserProfile'

# for some reason, cached sessions doesn't work with the debug toolbar
if DEBUG and DEBUG_TOOLBAR:
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
else:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Filters that are applied to an invalid variable will only be applied if
# TEMPLATE_STRING_IF_INVALID is set to '' (the empty string). If
# TEMPLATE_STRING_IF_INVALID is set to any other value, variable filters will
# be ignored.
# If TEMPLATE_STRING_IF_INVALID contains a '%s', the format marker will be
# replaced with the name of the invalid variable.

if DEBUG:
    # get django to throw an exception instead of silently include
    # the invalid template string.
    class InvalidString(str):
        def __mod__(self, other):
            from django.template.base import TemplateSyntaxError
            raise TemplateSyntaxError(
                "Undefined variable or unknown value for: %s" % repr(other))
    TEMPLATE_STRING_IF_INVALID = InvalidString("%s")
else:
    # in production mode, silently fail
    TEMPLATE_STRING_IF_INVALID = ''

# django-imagekit
IMAGEKIT_CACHEFILE_DIR = 'cache'
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'
IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'common.backends.ImageKitFileBackend'
IMAGEKIT_CACHE_BACKEND = 'default'
if S3_ENABLE:
    IMAGEKIT_DEFAULT_FILE_STORAGE = 'common.backends.ReducedRedundancyS3BotoStorage'
else:
    IMAGEKIT_DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# AWS Mechanical Turk
MTURK_PRODUCTION_HOST = u'mechanicalturk.amazonaws.com'
MTURK_SANDBOX_HOST = u'mechanicalturk.sandbox.amazonaws.com'
MTURK_HOST = MTURK_SANDBOX_HOST if MTURK_SANDBOX else MTURK_PRODUCTION_HOST
MTURK_COMMISSION = 0.10

#: Modules that contain MTurk experiments and ``configure_experiments`` or
#: ``update_changed_objects`` methods.
MTURK_MODULES = (
    'photos.experiments',
    'shapes.experiments',
    'bsdfs.experiments',
    'normals.experiments',
    'intrinsic.experiments',
)

# Captcha
CAPTCHA_CHALLENGE_FUNCT = 'common.utils.captcha_random_chars'
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_arcs',)

# Django Compressor
COMPRESS_ENABLED = True
COMPRESS_OUTPUT_DIR = 'cache'
#COMPRESS_STORAGE = STATICFILES_STORAGE
#COMPRESS_URL = STATIC_URL
#COMPRESS_ROOT = STATIC_ROOT
COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --bare --compile --stdio'),
    ('text/less', 'lessc -x {infile} {outfile}'),
)

# Paths of external utilities
import os.path
TRIANGULATE_BIN = os.path.realpath(os.path.join(
    SRC_DIR, os.pardir, 'triangulate', 'triangulate'))
CONVERT_OBJ_THREE_BIN = os.path.realpath(os.path.join(
    SRC_DIR, os.pardir, 'opt', 'three.js', 'utils', 'converters', 'obj',
    'convert_obj_three.py'))

# make matplotlib happy
os.environ['MPLCONFIGDIR'] = '/tmp'

# ipython
IPYTHON_ARGUMENTS = [
    '--ext', 'django_extensions.management.notebook_extension',
    '--profile=nbserver',
    #'--ipython-dir=/home/ubuntu/%s/.ipython' % server_user,
    #'--port=9999',
    #'--ip=*',
    #'--no-browser',
    #'--pylab=inline',
    #'--notebook-dir=/vol/labelmaterial/data/ipython-notebooks',
    #'--secure',
]
ADMIN_SHELL_PORT = 8888
ADMIN_SHELL_PASSWORD = 'opewut'

# Celery
CELERY_TIMEZONE = 'UTC'
CELERYD_MAX_TASKS_PER_CHILD = 1024
CELERY_ROUTES = {
    'mturk.tasks.intrinsic_decomposition_task': {'queue': 'intrinsic'},
    'mturk.tasks.intrinsic_decomposition_task_matlab': {'queue': 'matlab'},
    'intrinsic.tasks.import_ec2_task': {'queue': 'ec2'},
    'photo.tasks.add_photo_task': {'queue': 'local_server'},
}

if MTURK_PIPELINE_ENABLE:
    CELERYBEAT_SCHEDULE = {
        'mturk-iteration-every-10-minutes': {
            'task': 'mturk.tasks.mturk_iteration_task',
            'schedule': datetime.timedelta(minutes=10),
            #'args': (,)
        },
        'home-update-index-every-12-hours': {
            'task': 'home.tasks.update_index_context_task',
            'schedule': datetime.timedelta(hours=12),
            #'args': (,)
        }
    }
