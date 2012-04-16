from django.conf import settings
from mithril import set_current_ip
from django.utils.importlib import import_module

class WhitelistMiddleware(object):
    def get_strategy(self, django_settings=settings):
        lhs, rhs = getattr(django_settings, 'MITHRIL_STRATEGY').rsplit('.', 1)
        return getattr(import_module(lhs), rhs)() 

    def process_request(self, request):
        try:
            strategy = self.get_strategy()
            set_current_ip(strategy.get_ip_from_request(request))
        except AttributeError:
            pass

    def process_view(self, request, view, view_args, view_kwargs):
        if getattr(view, 'mithril_exempt', None):
            return None

        try:
            strategy = self.get_strategy()
            return strategy.process_view(request, view, *view_args, **view_kwargs)
        except AttributeError:
            pass
