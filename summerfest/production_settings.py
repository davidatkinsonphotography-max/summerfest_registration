"""
Production settings for Summerfest Registration System

Copy this file to settings_production.py and update with your actual values.
Never commit the actual production settings file to version control.
"""

import os
from .settings import *

# SECURITY WARNING: Generate a new secret key for production!
# You can generate one at: https://djecrety.ir/
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add your PythonAnywhere domain here
# Replace 'yourusername' with your actual PythonAnywhere username
ALLOWED_HOSTS = [
    'yourusername.pythonanywhere.com',
    'www.yourusername.pythonanywhere.com',
    'localhost',  # For testing
    '127.0.0.1',  # For testing
]

# Database
# For PythonAnywhere, you can use MySQL or PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'yourusername$summerfest',
#         'USER': 'yourusername',
#         'PASSWORD': os.environ.get('DB_PASSWORD'),
#         'HOST': 'yourusername.mysql.pythonanywhere-services.com',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }

# Security settings for HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files (CSS, JavaScript, Images)
# Replace 'yourusername' with your actual PythonAnywhere username
STATIC_ROOT = '/home/yourusername/summerfest_registration/static'
MEDIA_ROOT = '/home/yourusername/summerfest_registration/media'

# Stripe Configuration - LIVE KEYS FOR PRODUCTION!
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_live_YOUR_KEY_HERE')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_live_YOUR_KEY_HERE')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_YOUR_WEBHOOK_SECRET')

# Email Configuration for Production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your church's SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'summerfest@yourchurch.org')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'your-app-password')

# Default email settings
DEFAULT_FROM_EMAIL = 'Summerfest Registration <summerfest@yourchurch.org>'
SERVER_EMAIL = 'summerfest@yourchurch.org'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/yourusername/summerfest/logs/django.log',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Admin settings
ADMINS = [
    ('Admin', 'admin@yourchurch.org'),
]

MANAGERS = ADMINS

# Cache configuration (optional - improves performance)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/home/yourusername/summerfest/cache',
    }
}

# Session configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
