from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-#-bl8c4rg*&g)(%s+gdb9kwwmi82#$j^v@kkjdye2d=0^qdqin'

DEBUG = False  # ⚠️ Change to False before deploying to Render

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "linkzur.com",
    "www.linkzur.com",
]


# ✅ CORS setup
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True  # optional but often useful

# ✅ Media setup
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-party
    'corsheaders',
    'rest_framework',

    # local
    'linkzur_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ add this line

    'django.contrib.sessions.middleware.SessionMiddleware',
    
    'corsheaders.middleware.CorsMiddleware',  # ✅ must come before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Linkzur_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # ✅ Include React build for template lookup
        'DIRS': [BASE_DIR / 'frontend_build'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Linkzur_backend.wsgi.application'

# ✅ SQLite for local — fine for Render free tier
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ✅ Password validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ DRF & JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=3),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ✅ Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ✅ Static files — serves React build correctly
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'frontend_build' / 'static']  # React build static
STATIC_ROOT = BASE_DIR / 'staticfiles'  # where collectstatic collects
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'linkzur_app.CustomUser'

X_FRAME_OPTIONS = "ALLOWALL"

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    "http://localhost:8000",
    "http://127.0.0.1:8000",

    "https://linkzur.com",
    "https://www.linkzur.com",
]



# =============================
# EMAIL CONFIG (Zoho SMTP)
# =============================
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtppro.zoho.in")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))

EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True") == "True"
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False") == "True"

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "contact@linkzur.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "contact@linkzur.com")
