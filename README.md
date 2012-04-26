# Mithril

````

          ,--.  ,--.  ,--.            ,--.,--. 
,--,--,--.`--',-'  '-.|  ,---. ,--.--.`--'|  | 
|        |,--.'-.  .-'|  .-.  ||  .--',--.|  | 
|  |  |  ||  |  |  |  |  | |  ||  |   |  ||  | 
`--`--`--'`--'  `--'  `--' `--'`--'   `--'`--' 

````

A Django application providing decorators, middleware, and authentication
backends for IP whitelisting.

> ### WARNING
>
> We grab IP address information from `request.META` -- which is potentially
> spoofable. Make sure your gateway servers don't allow rewriting of the headers
> you're targeting.

## Getting Started

Mithril works by providing two new models -- `Whitelist` and `Range` -- that you
make a foreign key to from your objects. You define a `mithril.strategy.Strategy`
subclass to describe to mithril how you would like to obtain a `Whitelist` from
a request.

````python
# myapp/models.py
from django.db import models
from django.contrib.sites.models import Site
from mithril.models import Whitelist

class SiteACL(models.Model):
    site = models.OneToOneField(Site)
    whitelist = models.ForeignKey(Whitelist, related_name='site_acl')

# myapp/strategy.py
from mithril.strategy import Strategy
from django.conf import settings
from myapp.models import SiteACL

class MyStrategy(Strategy): 
    # a tuple of `method name` -> `lookup to apply`.
    # if the method does not exist, or returns None, it
    # continues to the next tuple.
    actions = (
        ('view_on_site', 'site_acl__pk')
    )

    def view_on_site(self, request, view, *view_args, **view_kwargs):
        try:
            site_acl = SiteACL.objects.get(site__pk=settings.SITE_ID)
            return site_acl.pk
        except SiteACL.DoesNotExist:
            pass 

# settings.py

MITHRIL_STRATEGY = 'myapp.strategy.MyStrategy'
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES) + ['mithril.middleware.WhitelistMiddleware']
INSTALLED_APPS = list(INSTALLED_APPS) + ['mithril']

````




