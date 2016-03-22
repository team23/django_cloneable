import os
import warnings
warnings.simplefilter('always')

test_dir = os.path.dirname(os.path.abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    },
}

USE_I18N = True
USE_L10N = True

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django_cloneable',
    'tests',
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

MIDDLEWARE_CLASSES = ()

TEMPLATE_DIRS = (
    os.path.join(test_dir, 'templates'),
)

STATIC_URL = '/static/'

SECRET_KEY = '0'

SITE_ID = 1
