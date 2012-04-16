from django.http import HttpResponseForbidden 
from django.utils.functional import curry
from mithril.models import Whitelist
import mithril

class Strategy(object):
    validate_whitelists = all
    forbidden_response_class = HttpResponseForbidden
    model = Whitelist

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

                response_fn = getattr(view, 'mithril_reset', None)
                if response_fn is None:
                    response_fn = self.forbidden_response_class
                else:
                    response_fn = curry(response_fn, args=(
                        request,
                        view,
                        args,
                        kwargs
                    ))

                return self.whitelist_ip(ip, whitelists, response_fn)

    def whitelist_ip(self, ip, whitelists, response_fn):
        okay = self.validate_whitelists(map(lambda w: w.okay(ip), whitelists))

        if not okay:
            return response_fn()

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

            # NB: Sometimes the cure is worse than the cold.
            # Django does some pretty "awesome" stuff to try and determine
            # which auth backend loaded a user. In this case, we only care
            # about new logins, so we make this generated class masquerade
            # as the class it's extending.
            #
            # That is to say: I am so, so sorry. 
            @property
            def __module__(self):
                return base_backend.__module__
    
            @property
            def __class__(self):
                return base_backend

        return MithrilBackend
