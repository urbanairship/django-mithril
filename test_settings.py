# (c) 2012 Urban Airship and Contributors

import os


DATABASES = {
    'default': {
        'NAME': 'project.db',
        'ENGINE': 'django.db.backends.sqlite3'
    }
}
# install the bare minimum for
# testing mithril
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'mithril',
)

# point to ourselves as the root urlconf, define no patterns (see below)
ROOT_URLCONF = 'test_settings'

# set this to turn off an annoying "you're doing it wrong" message
SECRET_KEY = 'lolwat'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(
                os.path.dirname(__file__),
                'mithril',
                'tests',
                'templates'
            )
        ],
        'APP_DIRS': True,
        'OPTIONS': {},
    },
]

# turn this file into a pseudo-urls.py.
from mithril import utils

if utils.pre_django_1_9():
    from django.conf.urls import patterns
    urlpatterns = patterns('')
else:
    urlpatterns = []
