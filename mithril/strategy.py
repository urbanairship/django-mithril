from django.http import HttpResponseForbidden 
from django.utils.functional import curry
from django.core.exceptions import FieldError
from django.core.urlresolvers import NoReverseMatch, reverse
from mithril.models import Whitelist
from mithril.signals import user_view_failed, user_login_failed
import mithril

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
                        )
                        return response
                    
    def whitelist_ip(self, ip, whitelists, response_fn):
        okay = False
        if ip is not None:
            okay = self.validate_whitelists(map(lambda w: w.okay(ip), whitelists))

        if not okay:
            return response_fn()

    @classmethod
    def get_authentication_backend(cls, base_backend, get_ip=mithril.get_current_ip):
        class MithrilBackend(base_backend):
            def authenticate(self, **kwargs):
                user = super(MithrilBackend, self).authenticate(**kwargs)

                if not cls.partial_credential_lookup:
                    return user

                for key, lookup in cls.partial_credential_lookup:
                    val = kwargs.get(key, None)
                    if val is not None:
                        whitelists = cls.model.objects.filter(**{lookup:val})

                        # XXX: this is a hack to get the current
                        # request IP by storing it in a well-known
                        # location during the ``process_request``
                        # portion of the middleware cycle.
                        ip = get_ip()
 
                        if cls.validate_whitelists(map(lambda w: w.okay(ip), whitelists)):
                            return user
                        else:
                            # that user shouldn't login!
                            cls.login_signal.send(
                                sender=self,
                                partial_credentials=val,
                                ip=ip
                            )
         
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
