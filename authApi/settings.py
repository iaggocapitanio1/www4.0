"""
In Sites can be the domains= activation, reset_password
"""
from pathlib import Path
from dotenv import load_dotenv
import os
from django.core.management.utils import get_random_secret_key
from datetime import timedelta


def str_to_bool(target) -> bool:
    if isinstance(target, bool):
        return target
    return target.lower() == 'true'


def mega_bytes_to_bits(mega: int) -> int:
    return mega * 1024 * 1024


PRODUCTION = True

if not PRODUCTION:
    load_dotenv('dev.env')
else:
    load_dotenv()

USE_X_FORWARDED_HOST = True

DEFAULT_PASSWORD = "changeMe"

DATA_UPLOAD_MAX_MEMORY_SIZE = mega_bytes_to_bits(mega=500)

WW4API_SKIP_ENTRYPOINT = str_to_bool(os.environ.get("WW4API_SKIP_ENTRYPOINT", False))

FORCE_SCRIPT_NAME = os.environ.get('WW4API_X_SCRIPT_NAME', default='')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CREATE_AS_ACTIVE = str_to_bool(os.environ.get("WW4API_CREATE_AS_ACTIVE", False))

SITE_ACTIVATION_DOMAIN_NAME = os.environ.get("WW4API_SITE_ACTIVATION_DOMAIN_NAME", default="activation")

SITE_RESET_PASSWORD_DOMAIN_NAME = os.environ.get("WW4API_SITE_RESET_PASSWORD_DOMAIN_NAME", default="reset-password")

REDIRECT_TO_FRONT = os.environ.get("WW4API_REDIRECT_TO_FRONT", False)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("WW4API_SECRET_KEY", get_random_secret_key())

PASSWORD_RESET_TIMEOUT = int(os.environ.get("WW4API_PASSWORD_RESET_TIMEOUT", default=50 * 60 * 60))  # 50 min

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

SESSION_COOKIE_AGE = int(os.environ.get("WW4API_SESSION_COOKIE_AGE", default=300 * 60 * 60))  # 5 hours

DEBUG = os.environ.get("WW4API_DEBUG", default="True") == "True"

ALLOWED_HOSTS = os.environ.get("WW4API_ALLOWED_HOSTS",
                               default="localhost,ww4,ww4api,woodwork4.ddns.net,127.0.0.1").split(',') + [
                    os.environ.get('X_FORWARDED_HOST', '')
                ]

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = {
    'rest_framework',
    'django_filters',
    'localflavor',
    'corsheaders',
    'oauth2_provider',
    'social_django',
    'drf_social_oauth2',
    'django_extensions',
    "whitenoise",
    'django_clamd',
    'protected_media.apps.ProtectedMediaConfig',
    'django_celery_beat',
    'django_celery_results',
    'mptt',
}
PROJECT_APPS = [
    'users.apps.UsersConfig',
    "permissions.apps.PermissionsConfig",
    "emailManager.apps.EmailmanagerConfig",
    "bucket.apps.BucketConfig",
    "chat.apps.ChatConfig",
    "tags.apps.TagsConfig",
    "entities.apps.EntitiesConfig"
]

INSTALLED_APPS = [
    *THIRD_PARTY_APPS,
    *DJANGO_APPS,
    *PROJECT_APPS
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'authApi.urls'

# Celery

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

CELERY_BROKER_URL = os.environ.get('WW4API_CELERY_BROKER_REDIS_URL', 'redis://localhost:6379')

CELERY_RESULT_BACKEND = os.environ.get('WW4API_CELERY_RESULT_BACKEND', 'redis://localhost:6379')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'authApi.wsgi.application'

if os.environ.get('WW4API_POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('WW4API_POSTGRES_DB', 'woodwork'),
            'USER': os.environ.get('WW4API_POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('WW4API_POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('WW4API_POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('WW4API_POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "users.User"

# Orion Settings

ORION_HOST = os.getenv("WW4API_ORION_HOST", default="http://localhost:1027")

ORION_ENTITIES = ORION_HOST + "/ngsi-ld/v1/entities"

NGSI_LD_CONTEXT = os.getenv("WW4API_CONTEXT", default="https://raw.githubusercontent.com/More-Collaborative"
                                                      "-Laboratory/ww4zero/main/context/ww4zero.context-ngsi.jsonld")

ORION_HEADERS = {
    'Content-Type': 'application/json; charset=utf-8',
    'Fiware-Service': 'woodwork40',
    'Link': f'<{NGSI_LD_CONTEXT}>; rel="http://www.w3.org/ns/json-ld#context;type="application/ld+json"'

}

KEYROCK_CLIENT = dict(
    TOKEN_URL=os.getenv("WW4API_KEYROCK_TOKEN_URL", default="http://localhost:3005/oauth2/token"),
    AUTHORIZE_URL=os.getenv("WW4API_KEYROCK_AUTHORIZE_URL"),
    CLIENT_ID=os.getenv("WW4API_KEYROCK_CLIENT_ID", default="tutorial-dckr-site-0000-xpresswebapp"),
    CLIENT_SECRET=os.getenv("WW4API_KEYROCK_CLIENT_SECRET", default="tutorial-dckr-site-0000-clientsecret"),
)

# HashField

HASHID_FIELD_SALT = os.getenv("WW4API_HASHID_FIELD_SALT", get_random_secret_key())

HASHID_FIELD_MIN_LENGTH = 16

HASHID_FIELD_BIG_MIN_LENGTH = 26

# Rest Framework

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5000/day',
        'user': '5000/day'
    },
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'drf_social_oauth2.authentication.SocialAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny', ],

    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 25,

    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# OAuth 2

AUTHENTICATION_BACKENDS = (

    # Facebook OAuth2
    'social_core.backends.facebook.FacebookAppOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',

    # drf_social_oauth2
    'drf_social_oauth2.backends.DjangoOAuth2',

    # Django
    'django.contrib.auth.backends.ModelBackend',
    'users.backends.EmailOrUsernameBackend'
)

# Facebook configuration
SOCIAL_AUTH_FACEBOOK_KEY = os.getenv("WW4API_SOCIAL_AUTH_FACEBOOK_KEY")

SOCIAL_AUTH_FACEBOOK_SECRET = os.getenv("WW4API_SOCIAL_AUTH_FACEBOOK_SECRET")

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, email'
}

DRF_SOCIAL_OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': timedelta(days=7).seconds,
    'REFRESH_TOKEN_EXPIRE_SECONDS': timedelta(days=14).seconds,  # 1 day
}
ACTIVATE_JWT = True

DRFSO2_URL_NAMESPACE = "drf"

# SPTM Email Server
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_USE_TLS = str_to_bool(os.getenv("WW4API_EMAIL_USE_TLS", default=True))

EMAIL_HOST = os.getenv("WW4API_EMAIL_HOST", "smtp.gmail.com")

EMAIL_PORT = os.getenv("WW4API_EMAIL_PORT", 587)

EMAIL_HOST_USER = os.getenv("WW4API_EMAIL_HOST_USER", "ww4wood@gmail.com")

EMAIL_HOST_PASSWORD = os.getenv("WW4API_EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = os.getenv("WW4API_DEFAULT_FROM_EMAIL", "ww4wood@gmail.com")

# ClamAV

CLAMD_SOCKET = os.getenv("CLAMD_SOCKET", default='/var/run/clamav/clamd.ctl')

CLAMD_USE_TCP = os.getenv("CLAMD_USE_TCP", False)

CLAMD_TCP_SOCKET = os.getenv("CLAMD_TCP_SOCKET", default=3310)

CLAMD_TCP_ADDR = os.getenv("CLAMD_TCP_ADDR", default='127.0.0.1')

# Cors

CORS_ALLOW_METHODS = os.getenv("WW4API_CORS_ALLOW_METHODS", default="DELETE,GET,OPTIONS,PATCH,POST,PUT").split(',')

ALLOWED_ORIGINS = os.getenv("WW4API_CORS_ALLOWED_ORIGINS", default="*").split(',')

if ALLOWED_ORIGINS == ["*"]:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = ALLOWED_ORIGINS

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "access_token",
    "Authorization",
    "x-requested-with",
    "connection"
]

SITE_ID = 1
# File Storage


STATIC_ROOT = BASE_DIR / os.getenv("WW4API_STATIC_ROOT_NAME", default="staticfiles")

STATIC_URL = os.getenv("WW4API_STATIC_URL", default='/static/')

STATIC_PATH = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = (
    STATIC_PATH,
)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = os.getenv("WW4API_MEDIA_URL", default='/media/')

# if FORCE_SCRIPT_NAME:
#     MEDIA_URL = FORCE_SCRIPT_NAME + MEDIA_URL

MEDIA_ROOT = BASE_DIR / os.getenv("WW4_MEDIA_ROOT_NAME", default='media/public/')

PROTECTED_MEDIA_ROOT = BASE_DIR / "media/protected/"

PROTECTED_MEDIA_URL = "/protected/"

PROTECTED_MEDIA_SERVER = os.getenv("WW4API_PROTECTED_MEDIA_SERVER", default="nginx")  # Defaults to

if FORCE_SCRIPT_NAME:
    PROTECTED_MEDIA_URL = FORCE_SCRIPT_NAME + PROTECTED_MEDIA_URL

PROTECTED_MEDIA_LOCATION_PREFIX = os.getenv("WW4API_PROTECTED_MEDIA_LOCATION_PREFIX", default="/internal")

PROTECTED_MEDIA_AS_DOWNLOADS = str_to_bool(os.getenv("WW4API_PROTECTED_MEDIA_AS_DOWNLOADS", default=False))

ADMIN = {
    "user": ["add", "view", "change", "delete"],
    "address": ["add", "view", "change", "delete"],
    "workerprofile": ["add", "view", "change", "delete"],
    "customerprofile": ["add", "view", "change", "delete"],
    "organizationprofile": ["add", "view", "change", "delete"],
    "group": ["add", "view", "change", "delete"],
    "permission": ["add", "view", "change", "delete"],
    "file": ["add", "view", "change", "delete"],
    "folder": ["add", "view", "change", "delete"],
    "tag": ["add", "view", "change", "delete"],
    "tagresult": ["add", "view", "change", "delete"],
}

ORION_ADMIN = {
    "assembly": ["add", "view", "change", "delete"],
    "leftover": ["add", "view", "change", "delete"],
    "budget": ["add", "view", "change", "delete"],
    "consumable": ["add", "view", "change", "delete"],
    "expedition": ["add", "view", "change", "delete"],
    "machine": ["add", "view", "change", "delete"],
    "organization": ["add", "view", "change", "delete"],
    "owner": ["add", "view", "change", "delete"],
    "part": ["add", "view", "change", "delete"],
    "project": ["add", "view", "change", "delete"],
    "worker": ["add", "view", "change", "delete"],
    "workerTask": ["add", "view", "change", "delete"],
    "machineTask": ["add", "view", "change", "delete"],
    "furniture": ["add", "view", "change", "delete"],
    "group": ["add", "view", "change", "delete"],
    "module": ["add", "view", "change", "delete"],

}

WORKER = {
    "user": ["add", "view", "add", "delete"],
    "address": ["add", "view", "add", "delete"],
    "workerprofile": ["add", "view", "add", "delete"],
    "customerprofile": ["add", "view", "add", "delete"],
    "organizationprofile": ["view"],
    "group": ["add", "view", "change", "delete"],
    "file": ["add", "view", "change", "delete"],
    "folder": ["add", "view", "change", "delete"],
    "tag": ["add", "view", "change", "delete"],
    "tagresult": ["add", "view", "change", "delete"],
    "permission": ["add", "view", "change", "delete"],
}

ORION_ALL_PERMISSIONS = {
    "assembly": ["add", "view", "change", "delete"],
    "leftover": ["add", "view", "change", "delete"],
    "budget": ["add", "view", "change", "delete"],
    "consumable": ["add", "view", "change", "delete"],
    "expedition": ["add", "view", "change", "delete"],
    "machine": ["add", "view", "change", "delete"],
    "organization": ["add", "view", "change", "delete"],
    "owner": ["add", "view", "change", "delete"],
    "part": ["add", "view", "change", "delete"],
    "project": ["add", "view", "change", "delete"],
    "worker": ["add", "view", "change", "delete"],
    "workerTask": ["add", "view", "change", "delete"],
    "machineTask": ["add", "view", "change", "delete"],
    "furniture": ["add", "view", "change", "delete"],
    "group": ["add", "view", "change", "delete"],
    "module": ["add", "view", "change", "delete"],

}

ORION_WORKER = {
    "assembly": ["add", "view", "change", "delete"],
    "leftover": ["add", "view", "change", "delete"],
    "budget": ["add", "view", "change", "delete"],
    "consumable": ["add", "view", "change", "delete"],
    "expedition": ["add", "view", "change", "delete"],
    "machine": ["add", "view", "change", "delete"],
    "organization": ["view"],
    "owner": ["add", "view", "change", "delete"],
    "part": ["add", "view", "change", "delete"],
    "project": ["add", "view", "change", "delete"],
    "worker": ["add", "view", "change", "delete"],
    "group": ["add", "view", "change", "delete"],
    "module": ["add", "view", "change", "delete"],
    "workerTask": ["add", "view", "change", "delete"],
    "machineTask": ["add", "view", "change", "delete"],
    "furniture": ["add", "view", "change", "delete"],

}

CUSTOMER = {
    "user": ["view", "add", "delete"],
    "address": ["add", "view", "add", "delete"],
    "workerprofile": [],
    "customerprofile": ["view", "add", "delete"],
    "organizationprofile": [],
    "group": ["view"],
    "file": ["view", "add"],
    "folder": ["view"],
    "workerTask": [],
    "machineTask": [],
    "furniture": ["view"],
    "tag": [],
    "tagresult": [],
}

ORION_CUSTOMER = {
    "assembly": ["view"],
    "leftover": [],
    "budget": ["view"],
    "consumable": [],
    "expedition": ["view"],
    "machine": [],
    "organization": [],
    "owner": ["add", "view", "change", "delete"],
    "part": ["view"],
    "project": ["view"],
    "worker": [],
    "group": [],
    "workerTask": [],
    "machineTask": [],
    "furniture": [],
    "module": [],

}

LOG_DIR = BASE_DIR.joinpath('logs')

LOG_DIR.mkdir(parents=True, exist_ok=True)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR.joinpath('woodWork40.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'chat': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            "propagate": True
        },
    },
}

OAUTH2_PROVIDER = {
    "SCOPES": {
        "ww4": "WW4 scope",
        'read': 'Read scope',
        'write': 'Write scope',
        'delete': 'Delete scope'
    },
    'ACCESS_TOKEN_EXPIRE_SECONDS': timedelta(days=7).seconds,  # 1 hour
    'REFRESH_TOKEN_EXPIRE_SECONDS': timedelta(days=14).seconds,  # 1 day
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': timedelta(days=7).total_seconds(),  # Set the token expiration time as desired
}