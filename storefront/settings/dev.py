from .common import *

DEBUG = True

SECRET_KEY = 'django-insecure-c=h15f3w!8wft29@=uhr!m_vsg2c0vh#o$n)0y!7+)y$5m)nf='


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'store',
        'USER': 'root',
        'PASSWORD': 'A_ahmed0507504984',
        'HOST': 'localhost',
    }
}
