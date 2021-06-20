from datetime import timedelta
from django.contrib.messages import constants as messages

from .base import *


# GLOBAL CONFIGURATIONS
APP_NAME = 'Mini Loka'
PROJECT_URL = 'www.miniloka.com'
PAGINATION_PER_PAGE = 20
LOGOUT_REDIRECT_URL = '/'
# If true in recovery password inquiry make sure account exist
RECOVERY_PASSWORD_CHECK_ACCOUNT = True
DISTANCE_RADIUS = 15


# REGISTRATION REQUIREMENTS
USER_EMAIL_FIELD = 'email'
USER_MSISDN_FIELD = 'msisdn'
USER_REQUIRED_VERIFICATION = True
USER_VERIFICATION_FIELDS = ['email', 'msisdn']


# FIREBASE
FCM_SERVER_KEY = 'AAAA_LD_cFU:APA91bEa4DNFgSAd9WMEA-8xenfsI2_65oMiTh4AhpF9kX1B8ngq-O7Y4vLKIavfCPqv1zAk13GHjoArA0ZwAQOSuPU8Xp9fszzW3vf6aj1gqpeIWgSwicTWIy2fQj-VB71NQxIEEwKh'


# Application definition
PROJECT_APPS = [
    'channels',
    'corsheaders',
    'rest_framework',
    'django_filters',
    'taggit',
    'simple_history',
    'apps.person',
    'apps.procure',
]
INSTALLED_APPS = INSTALLED_APPS + PROJECT_APPS


# MIDDLEWARES
PROJECT_MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    # 'apps.person.utils.middleware.AuthMiddleware',
]
MIDDLEWARE = PROJECT_MIDDLEWARE + MIDDLEWARE


# Specifying authentication backends
# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/
AUTHENTICATION_BACKENDS = ['apps.person.utils.auth.LoginBackend', ]


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#auth-custom-user
AUTH_USER_MODEL = 'person.User'


# CACHING
# https://docs.djangoproject.com/en/2.2/topics/cache/
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '10.0.2.2:11211',
        'OPTIONS': {
            'server_max_value_length': 1024 * 1024 * 2,
        },
        'KEY_PREFIX': 'miniloka_cache'
    }
}


# MESSAGES
# https://docs.djangoproject.com/en/3.0/ref/contrib/messages/
MESSAGE_TAGS = {
    messages.DEBUG: 'alert alert-dark shadow-sm',
    messages.INFO: 'alert alert-info shadow-sm',
    messages.SUCCESS: 'alert alert-info success shadow-sm',
    messages.WARNING: 'alert alert-warning shadow-sm',
    messages.ERROR: 'alert alert-error shadow-sm',
}


# Django Sessions
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/settings/
SESSION_SAVE_EVERY_REQUEST = False
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# Django Simple JWT
# ------------------------------------------------------------------------------
# https://github.com/davesque/django-rest-framework-simplejwt
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
    'USER_ID_FIELD': 'uuid',
    'USER_ID_CLAIM': 'user_uuid',
}


# Django Rest Framework (DRF)
# ------------------------------------------------------------------------------
# https://www.django-rest-framework.org/
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # for mobile apps this must removed
        # 'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': PAGINATION_PER_PAGE
}


# Email Configuration
# https://docs.djangoproject.com/en/3.0/topics/email/
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


# REDIS
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'
REDIS_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT


# SENDGRID
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = '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'
EMAIL_PORT = 587
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False


# Django-taggit
# https: // django-taggit.readthedocs.io/en/latest/getting_started.html
TAGGIT_CASE_INSENSITIVE = True
