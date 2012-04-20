# (c) 2012 Urban Airship and Contributors

from django.conf import settings
from mithril import set_current_ip
from django.utils.importlib import import_module


class WhitelistMiddleware(object):

    def get_strategy(self, django_settings=settings):
        lhs, rhs = getattr(django_settings, 'MITHRIL_STRATEGY').rsplit('.', 1)
        return getattr(import_module(lhs), rhs)() 

    def process_request(self, request, set_ip=set_current_ip):
        # no matter what, clear the current IP.
        set_ip(None)
        try:
            strategy = self.get_strategy()
        except AttributeError:
            pass
        else:
            set_ip(strategy.get_ip_from_request(request))

    def process_view(self, request, view, view_args, view_kwargs):
        if getattr(view, 'mithril_exempt', None):
            return None

        try:
            strategy = self.get_strategy()
        except AttributeError:
            pass
        else:
            return strategy.process_view(
                    request, view, *view_args, **view_kwargs)
