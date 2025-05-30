# This file is part of LOVE-manager.
#
# Copyright (c) 2023 Inria Chile.
#
# Developed by Inria Chile.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or at
# your option any later version.
#
# This program is distributed in the hope that it will be useful,but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""
Django settings for manager project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

import ldap
from django_auth_ldap.config import LDAPSearch

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# Define the max file size for user uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880

# Define the URL subpath for this application when deployed:
FORCE_SCRIPT_NAME = os.environ.get("URL_SUBPATH")

# Define the type of storage to use for media files: remote or local
DEFAULT_FILE_STORAGE = (
    "manager.utils.RemoteStorage"
    if os.environ.get("REMOTE_STORAGE")
    else "django.core.files.storage.FileSystemStorage"
)

# Define the default auto field for Django models
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define wether the system is being tested or not:
TESTING = os.environ.get("TESTING", False)
"""Define wether or not this instance is being created for testing or not,
get from the `TESTING` environment variable (`string`)"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "tbder3gzppu)kl%(u3awhhg^^zu#j&!ceh@$n&v0d38sjx43s8"
)
"""Secret Key for Django, read from the `SECRET_KEY`
environment variable (`string`)"""

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ.get("NO_DEBUG"):
    DEBUG = False
else:
    DEBUG = True

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
if os.environ.get("DB_ENGINE") == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "postgres"),
            "USER": os.getenv("DB_USER", "postgres"),
            "HOST": os.getenv("DB_HOST", "postgres"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "PASSWORD": os.getenv("DB_PASS", "postgres"),
        }
    }
    """Databases configuration (`dict`)"""
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

SERVER_URL = os.environ.get("SERVER_URL", None)
ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "love-nginx-mount",
    "love-nginx",
    SERVER_URL,
]
CSRF_TRUSTED_ORIGINS = [f"https://{SERVER_URL}", f"http://{SERVER_URL}"]
"""List of Django allowed hosts (`list` of `string`)"""

# Application definition
INSTALLED_APPS = [
    "daphne",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 'webpack_loader',
    "channels",
    "rest_framework",
    # 'rest_framework.authtoken',
    "corsheaders",
    "drf_yasg",
    "api",
    "subscription",
    "ui_framework",
    "redirect",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "api.middleware.GetTokenMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "manager.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# CORS Configuration
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

WSGI_APPLICATION = "manager.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Password for other processes
PROCESS_CONNECTION_PASS = os.environ.get("PROCESS_CONNECTION_PASS", "dev_pass")
"""Password that Producers use to connect to eh Manager,
read from the `PROCESS_CONNECTION_PASS` environment variable (`string`)"""

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"
"""Language of the Django app (`string`)"""

TIME_ZONE = "UTC"
"""Timezone of the Django app (`string`)"""

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.DjangoModelPermissions",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.authentication.ExpiringTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
}

TOKEN_EXPIRED_AFTER_DAYS = 30
"""Duration of users tokens, in days (`int`)"""


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = (
    f"{FORCE_SCRIPT_NAME}/manager/static/" if FORCE_SCRIPT_NAME else "/manager/static/"
)

"""URL to access Django static files (`string`)"""

STATIC_ROOT = os.path.join(BASE_DIR, "static")
"""Location of static files (`string`)"""

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static_files"),
]

MEDIA_URL = (
    f"{FORCE_SCRIPT_NAME}/manager/media/" if FORCE_SCRIPT_NAME else "/manager/media/"
)
"""URL for media files access (`string`)"""
MEDIA_BASE = BASE_DIR
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Channels
ASGI_APPLICATION = "manager.routing.application"
REDIS_HOST = os.environ.get("REDIS_HOST", False)
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_PASS = os.environ.get("REDIS_PASS", False)
REDIS_CONFIG_EXPIRY = int(os.environ.get("REDIS_CONFIG_EXPIRY", 60))
REDIS_CONFIG_CAPACITY = int(os.environ.get("REDIS_CONFIG_CAPACITY", 100))
REDIS_CONFIG_GROUP_EXPIRY = int(os.environ.get("REDIS_CONFIG_GROUP_EXPIRY", 43200))
if REDIS_HOST and not TESTING:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [
                    "redis://:"
                    + REDIS_PASS
                    + "@"
                    + REDIS_HOST
                    + ":"
                    + REDIS_PORT
                    + "/0"
                ],
                "expiry": REDIS_CONFIG_EXPIRY,
                "capacity": REDIS_CONFIG_CAPACITY,
                "group_expiry": REDIS_CONFIG_GROUP_EXPIRY,
            },
        },
    }
    """Django Channels Channel Layer configuration (`dict`)"""

else:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# LDAP
# Baseline configuration:
AUTH_LDAP_1_SERVER_URI = os.environ.get("AUTH_LDAP_1_SERVER_URI")
AUTH_LDAP_2_SERVER_URI = os.environ.get("AUTH_LDAP_2_SERVER_URI")
AUTH_LDAP_3_SERVER_URI = os.environ.get("AUTH_LDAP_3_SERVER_URI")
"""URL for the LDAP server. Read from `AUTH_LDAP_SERVER_URI`
environment variable (`bool`)"""

# Only use LDAP activation backend if there is an AUTH_LDAP_SERVER_URI
AUTH_LDAP_BIND_DN = "uid=svc_love,cn=users,cn=accounts,dc=lsst,dc=cloud"
AUTH_LDAP_BIND_PASSWORD = os.environ.get("AUTH_LDAP_BIND_PASSWORD")
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "cn=users,cn=accounts,dc=lsst,dc=cloud",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)",
)
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenname",
    "last_name": "sn",
    "email": "mail",
}
if AUTH_LDAP_3_SERVER_URI:
    AUTHENTICATION_BACKENDS.insert(0, "api.views.IPABackend3")
    AUTH_LDAP_3_BIND_DN = AUTH_LDAP_BIND_DN
    AUTH_LDAP_3_BIND_PASSWORD = AUTH_LDAP_BIND_PASSWORD
    AUTH_LDAP_3_USER_SEARCH = AUTH_LDAP_USER_SEARCH
    AUTH_LDAP_3_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP

if AUTH_LDAP_2_SERVER_URI:
    AUTHENTICATION_BACKENDS.insert(0, "api.views.IPABackend2")
    AUTH_LDAP_2_BIND_DN = AUTH_LDAP_BIND_DN
    AUTH_LDAP_2_BIND_PASSWORD = AUTH_LDAP_BIND_PASSWORD
    AUTH_LDAP_2_USER_SEARCH = AUTH_LDAP_USER_SEARCH
    AUTH_LDAP_2_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP

if AUTH_LDAP_1_SERVER_URI:
    AUTHENTICATION_BACKENDS.insert(0, "api.views.IPABackend1")
    AUTH_LDAP_1_BIND_DN = AUTH_LDAP_BIND_DN
    AUTH_LDAP_1_BIND_PASSWORD = AUTH_LDAP_BIND_PASSWORD
    AUTH_LDAP_1_USER_SEARCH = AUTH_LDAP_USER_SEARCH
    AUTH_LDAP_1_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP

TRACE_TIMESTAMPS = True
"""Define wether or not to add tracing timestamps to websocket messages.
Read from TRACE_TIMESTAMPS` environment variable (`bool`)"""

if os.environ.get("HIDE_TRACE_TIMESTAMPS", False):
    TRACE_TIMESTAMPS = False

# Check HeartBeat Commanded
HEARTBEAT_QUERY_COMMANDER = (
    os.environ.get("HEARTBEAT_QUERY_COMMANDER", "true").lower() == "true"
)

# LOVE-PRODUCER-CONFIGURATION
"""Defines wether or not ussing the legacy LOVE-producer version,
i.e. not the LOVE CSC Producer"""
LOVE_PRODUCER_LEGACY = os.environ.get("LOVE_PRODUCER_LEGACY", False)


# Get permision type configuration
COMMANDING_PERMISSION_TYPE = os.environ.get(
    "COMMANDING_PERMISSION_TYPE", "user"
).lower()
