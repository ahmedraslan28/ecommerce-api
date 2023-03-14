from .common import *

DEBUG = True

SECRET_KEY = 'django-insecure-c=h15f3w!8wft29@=uhr!m_vsg2c0vh#o$n)0y!7+)y$5m)nf='

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'store',
        'USER': 'root',
        'PASSWORD': 'A_ahmed0507504984',
        'HOST': 'localhost',
    }
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 2525
DEFAULT_FROM_EMAIL = 'admin@example.com'
