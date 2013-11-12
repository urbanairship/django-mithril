# (c) 2012 Urban Airship and Contributors

from django.conf import settings
from django.core.exceptions import FieldError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.http import HttpResponseForbidden 
from django.utils.functional import curry

from mithril.models import Whitelist, CachedWhitelist
from mithril.signals import user_view_failed, user_login_failed


class Strategy(object):

    validate_whitelists = all
    forbidden_response_class = HttpResponseForbidden
    model = Whitelist

    view_signal = user_view_failed
    login_signal = user_login_failed

    actions = []
    partial_credential_lookup = []
    request_ip_headers = (
        'REMOTE_ADDR',
    )

    def get_ip_from_request(self, request):
        for header in self.request_ip_headers:
            if request.META.get(header, None) is not None:
                return request.META[header]
        return None

    def process_view(self, request, view, *args, **kwargs):

        # Superusers get exempted.
        is_superuser = getattr(request.user, 'is_superuser', None)
        if is_superuser:
            return None

        ip = self.get_ip_from_request(request)
        for predicate, lookup in self.actions:
            method = getattr(self, predicate, None)
            if method is not None:
                value = method(request, view, *args, **kwargs)
                if value is None:
                    continue

                try:
                    whitelists = self.model.objects.filter(**{lookup:value})
                    if not len(whitelists):
                        continue
                except FieldError:
                    continue
                else:
                    response_fn = getattr(view, 'mithril_reset', None)
                    if response_fn is None:
                        response_fn = self.forbidden_response_class
                    else:
                        response_fn = curry(response_fn,
                            request,
                            view,
                            args,
                            kwargs
                        )

                    response = self.whitelist_ip(ip, whitelists, response_fn)
                    if response is not None:
                        try:
                            url = reverse(
                                view,
                                args=args,
                                kwargs=kwargs
                            )   
                        except NoReverseMatch:
                            url = None

                        self.view_signal.send(
                            sender=self,
                            user=request.user,
                            url=url,
                            ip=ip,
                            whitelists=whitelists,
                        )
                        return response

    def whitelist_ip(self, ip, whitelists, response_fn):
        okay = False
        if ip is not None:
            okay = self.validate_whitelists(
                    map(lambda w: w.okay(ip), whitelists))

        if not okay:
            return response_fn()


class CachedStrategy(Strategy):
    model = CachedWhitelist


def get_strategy_from_settings():
    """ Get the strategy class defined in Django settings

    Relies upon configuration value ``MITHRIL_STRATEGY``.

    """
    path = settings.MITHRIL_STRATEGY
    mod = __import__('.'.join(path.split('.')[:-1]))
    components = path.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
