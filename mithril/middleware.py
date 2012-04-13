from django.conf import settings
from django.http import HttpResponseForbidden


__all__ = ( 
    'IPWhitelistAllMiddleware',
    'IPWhitelistAnyMiddleware',
)

LOOKUPS_SETTING = 'MITHRIL_WHITELIST_TO_USER_LOOKUPS' 
HEADERS_SETTING = 'MITHRIL_WHITELIST_IP_HEADER'

MITHRIL_WHITELIST_TO_USER_LOOKUPS = (
    'company__granted_perm__user',
    'company__admins__user',
)

MITHRIL_WHITELIST_IP_HEADER = (
    'HTTP_TRUE_IP',
    'HTTP_X_FORWARDED_FOR',
    'REMOTE_ADDR'
)


class IPWhitelistMiddleware(object):
    """Match incoming user against whitelists for any company/organization."""

    # default behavior is that an ip must pass
    # "all" whitelists to be applicable
    behavior = all

    def ip_from_request(request):
        headers = getattr(settings, HEADERS_SETTING, [])
        for header_name in headers:
            ip = request.META.get(header_name, None)
            if ip is not None:
                return ip

    def ip_in_whitelists(self, ip, whitelists):
        return self.behavior(
                lambda r : self.ip_in_whitelist(ip, r), whitelists)

    def ip_in_whitelist(self, ip, whitelist):
        return whitelist.okay(ip)

    def get_applicable_whitelists(self, request):
        user = request.user
        whitelist_to_user_lookups = getattr(settings, LOOKUPS_SETTING, [])

        whitelists = []
        for lookup in whitelist_to_user_lookups:
            whitelists.append(
                whitelist_to_user_lookups.objects.filter(**{
                    lookup:user
                })[:]
            )

        return whitelists

    def process_request(self, request, *args, **kwargs):
        try:
            whitelists = self.get_applicable_whitelists(request)
            ip = self.ip_from_request(request)
            is_valid_ip = self.ip_in_whitelists(ip, whitelists)
            return self.whitelist(ip, is_valid_ip, whitelists)
        except AttributeError:
            return None  

    def whitelist(self, ip, is_valid, whitelists):
        """Return 403 if user doesn't match criteria.

        Returns:
            HttpResponseForbidden if user is subject to whitelist, and None 
            otherwise.
        """
        if not is_valid:
            return HttpResponseForbidden(
            ('You are accessing this account from an IP '
            'outside the configured ranges'))
        else:
            return None


class IPWhitelistAllMiddleware(IPWhitelistMiddleware):
    behavior = all


class IPWhitelistAnyMiddleware(IPWhitelistMiddleware):

    # if it passes any whitelist, it's valid.
    behavior = any

