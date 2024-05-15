import os
from pathlib import Path
from typing import List, Optional, Tuple

import django_stubs_ext

django_stubs_ext.monkeypatch()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_ROOT = str(BASE_DIR) + "/media/"
MEDIA_URL = "media/"

# keep files up to 10MB in memory instead of writing temp files
# when using upload handlers
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# set DEBUG to true by default (technically insecure, but easier for development)
DEBUG = int(os.environ.get("DEBUG", 1))

# load some env vars with dev defaults
SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
ALLOWED_HOSTS: List[str] = list(filter(None, os.environ.get("ALLOWED_HOSTS", "").split(",")))
CSRF_COOKIE_SECURE = int(os.environ.get("SECURE_COOKIE", 0))
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE

# set reverse proxy protocol header
SECURE_PROXY_SSL_HEADER: Optional[Tuple[str, str]]
if secure_proxy_header := os.environ.get("SECURE_PROXY_HEADER"):
    SECURE_PROXY_SSL_HEADER = (f"HTTP_{secure_proxy_header}", "https")
else:
    SECURE_PROXY_SSL_HEADER = None

# set some debugging defaults if running in debug mode, otherwise require most values to be set
if DEBUG:
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = SECRET_KEY or "django-insecure-tri6o0xj)y+so6y380=5)jes##^d9tf-vk+6n0%+zh3i=a8b-o"
    ALLOWED_HOSTS = ALLOWED_HOSTS or []
else:
    assert SECRET_KEY
    assert ALLOWED_HOSTS
    assert CSRF_COOKIE_SECURE and SESSION_COOKIE_SECURE
    assert SECURE_PROXY_SSL_HEADER


# Application definition

INSTALLED_APPS = [
    "model.apps.ModelConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "api",
    "client",
]

if DEBUG:
    INSTALLED_APPS.append("django_extensions")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "pitshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "pitshop.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "model.ExtendedUser"

LOGIN_URL = "client:login"


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "de"

TIME_ZONE = "CET"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "global_static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


######

LASERCUT_PREVIEW_ENDPOINT = os.environ.get("LASERCUT_PREVIEW_ENDPOINT", "http://127.0.0.1:6472")
