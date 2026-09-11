from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-for-production"
)

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if h.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "services",
    "dashboard",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        }
    }
]

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DB_ENGINE = os.getenv(
    "DJANGO_DB_ENGINE",
    "sqlite3"
).strip().lower()

if DB_ENGINE == "oracle":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.oracle",
            "NAME": os.getenv(
                "ORACLE_DSN",
                "localhost:1521/ORCLPDB"
            ),
            "USER": os.getenv("ORACLE_USER", ""),
            "PASSWORD": os.getenv("ORACLE_PASSWORD", ""),
        }
    }

elif DB_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv(
                "POSTGRES_DB",
                "sahyog_db"
            ),
            "USER": os.getenv(
                "POSTGRES_USER",
                "sahyog_user"
            ),
            "PASSWORD": os.getenv(
                "POSTGRES_PASSWORD",
                "Sahyog@2026"
            ),
            "HOST": os.getenv(
                "POSTGRES_HOST",
                "localhost"
            ),
            "PORT": os.getenv(
                "POSTGRES_PORT",
                "5432"
            ),
        }
    }

else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en"

TIME_ZONE = os.getenv(
    "DJANGO_TIME_ZONE",
    "Asia/Kolkata"
)

USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("hi", "हिन्दी"),
    ("bn", "বাংলা"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale"
]


# ============================================================
# STATIC / MEDIA
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static"
]

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# DJANGO DEFAULTS
# ============================================================

LOGIN_URL = "login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# EMAIL / GMAIL SMTP
# ============================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv(
    "EMAIL_HOST_USER",
    ""
)

EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    ""
)

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# ============================================================
# MAPBOX
# ============================================================

MAPBOX_ACCESS_TOKEN = os.getenv(
    "MAPBOX_ACCESS_TOKEN",
    ""
)

MAPBOX_STYLE = os.getenv(
    "MAPBOX_STYLE",
    "mapbox://styles/mapbox/streets-v12"
)


# ============================================================
# RAZORPAY
# ============================================================

RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID",
    ""
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET",
    ""
)

RAZORPAY_WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET",
    ""
)


# ============================================================
# GOOGLE OAUTH
# ============================================================

GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    ""
)

GOOGLE_CLIENT_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET",
    ""
)

GOOGLE_OAUTH_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI",
    ""
)


# ============================================================
# PLATFORM
# ============================================================

PLATFORM_FEE_PERCENT = float(
    os.getenv(
        "PLATFORM_FEE_PERCENT",
        "5"
    )
)


# ============================================================
# PRODUCTION / SECURITY SETTINGS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    u.strip()
    for u in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        ""
    ).split(",")
    if u.strip()
]

SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if os.getenv(
        "DJANGO_BEHIND_PROXY",
        "0"
    ) == "1"
    else None
)

SESSION_COOKIE_SECURE = (
    os.getenv(
        "DJANGO_SESSION_COOKIE_SECURE",
        "0"
    ) == "1"
)

CSRF_COOKIE_SECURE = (
    os.getenv(
        "DJANGO_CSRF_COOKIE_SECURE",
        "0"
    ) == "1"
)