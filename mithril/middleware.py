from django.conf import settings
from mithril import set_current_ip

class WhitelistMiddleware(object):
    def get_strategy(self, django_settings=settings):
        return getattr(django_settings, 'MITHRIL_STRATEGY', None)()

    def process_request(self, request):
        try:
            strategy = self.get_strategy()
            set_current_ip(strategy.get_ip_from_request(request))
        except TypeError:
            pass

    def process_view(self, request, view, *args, **kwargs):
        if getattr(view, 'mithril_exempt'):
            return None

        try:
            strategy = self.get_strategy()
            return strategy.process_view(request, view, *args, **kwargs)
        except TypeError:
            pass
