"""
Django settings for Corazon Marketplace project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# In production, set this via an environment variable instead.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-t=qb%7_u3s)p(gdtb&c8g%psby+(3=4azfnve=+0uadf49rna&'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Corazon Marketplace apps
    'accounts',
    'products',
    'cart',
    'orders',
    'jobs',
    'loyalty',
    'marketing',
    'agents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.ReferralTrackingMiddleware',
]

ROOT_URLCONF = 'corazon.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart_summary',
                'products.context_processors.all_categories',
                'loyalty.context_processors.loyalty_balance',
                'accounts.context_processors.pending_approvals',
            ],
        },
    },
]

WSGI_APPLICATION = 'corazon.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (product images, resumes)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'products:home'
LOGOUT_REDIRECT_URL = 'products:home'

# Max upload size (5 MB) for resumes / product images
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# ----------------------------------------------------------------------
# Email — used to notify the site admin/manager when someone submits the
# Advertise With Us inquiry form (see marketing.notifications).
#
# By default this uses Django's console backend: "sending" an email just
# prints it to the terminal/server log running `runserver`. That's fine
# for local testing but is NOT real email delivery. To actually receive
# these by email, set real SMTP credentials via environment variables
# (e.g. a Gmail account with an App Password, or a transactional email
# provider like SendGrid/Mailgun/Brevo) and this will switch over
# automatically — no code changes needed:
#
#   export DJANGO_EMAIL_HOST=smtp.gmail.com
#   export DJANGO_EMAIL_PORT=587
#   export DJANGO_EMAIL_USE_TLS=True
#   export DJANGO_EMAIL_HOST_USER=you@gmail.com
#   export DJANGO_EMAIL_HOST_PASSWORD=your-app-password
#   export DJANGO_ADMIN_NOTIFICATION_EMAIL=manager@yourcompany.com
# ----------------------------------------------------------------------
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', '')

if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('DJANGO_EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD', '')
else:
    # No SMTP configured — print emails to the console instead of failing.
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'noreply@corazonmarketplace.example')

# Who receives inquiry notifications. Defaults to a placeholder — set
# DJANGO_ADMIN_NOTIFICATION_EMAIL in production, or change this directly.
ADMIN_NOTIFICATION_EMAIL = os.environ.get('DJANGO_ADMIN_NOTIFICATION_EMAIL', 'admin@corazonmarketplace.example')
