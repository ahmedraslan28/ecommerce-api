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
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ahmedraslan28@gmail.com'
EMAIL_HOST_PASSWORD = 'gofzyeekksxsltju'
