DATABASES = {'default':{
    'NAME':'project.db',
    'ENGINE':'django.db.backends.sqlite3'
}}
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'mithril',
)
ROOT_URLCONF = 'test_settings'

from django.conf.urls.defaults import *

urlpatterns = patterns('')
