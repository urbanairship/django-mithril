from django.http import HttpResponseForbidden 
from mithril.models import Whitelist
import mithril

class Strategy(object):
    validate_whitelists = all
    forbidden_response_class = HttpResponseForbidden
    model = Whitelist

    def get_ip_from_request(self, request):
        for header in self.request_ip_headers:
            if request.META.get(header, None) is not None:
                return request.META[header]
        return None

    def process_view(self, request, view, *args, **kwargs):
        ip = self.get_ip_from_request(request)
        for predicate, lookup in self.actions:
            method = getattr(self, predicate, None)
            if method is not None:
                value = method(request, view, *args, **kwargs)
                if value is None:
                    continue

                whitelists = self.model.objects.filter(**{lookup:value})
                if not len(whitelists):
                    continue

                return self.whitelist_ip(ip, whitelists)

    def whitelist_ip(self, ip, whitelists):
        okay = self.validate_whitelists(map(lambda w: w.okay(ip), whitelists))

        if not okay:
            return self.forbidden_response_class()

    @classmethod
    def get_authentication_backend(cls, base_backend, get_ip=mithril.get_current_ip):
        class MithrilBackend(base_backend):
            def authenticate(self, **kwargs):
                user = super(MithrilBackend, self).authenticate(**kwargs)
                for key, lookup in cls.partial_credential_lookup:
                    val = kwargs.get(key, None)
                    if val:
                        whitelists = cls.model.objects.filter(**{lookup:val})

                        # XXX: this is a hack to get the current
                        # request IP by storing it in a well-known
                        # location during the ``process_request``
                        # portion of the middleware cycle.
                        ip = get_ip()
 
                        if cls.validate_whitelists(map(lambda w: w.okay(ip), whitelists)):
                            return user

        return MithrilBackend
