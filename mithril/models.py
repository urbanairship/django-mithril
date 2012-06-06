# (c) 2012 Urban Airship and Contributors

from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.utils import simplejson as json
import netaddr

class CachedWhitelistManager(models.Manager):
    cache_timeout = getattr(settings, 'MITHRIL_CACHE_TIMEOUT', 60 * 30)

    def create(self, **kwargs):
        super_create = super(CachedWhitelistManager, self).create

        obj = super_create(**kwargs)

        reverse_key = self.make_reverse_cache_key(obj)
        reverse_val = cache.get(reverse_key)

        if reverse_val is not None:
            cache.delete(reverse_val)
            cache.delete(reverse_key)

        return obj

    def filter(self, **kwargs):
        super_filter = super(CachedWhitelistManager, self).filter
        try:
            lookup, value = kwargs.items()[0]
        except ValueError:
            return super_filter(**kwargs)

        if isinstance(value, models.Model):
            lookup = '%s__pk' % lookup
            value = value.pk

        key = self.make_cache_key(lookup, value)
        cache_val = cache.get(key)

        if cache_val is None:
            cache_val = [{
                'name': whitelist.name,
                'slug': whitelist.slug,
                'ranges': whitelist.ranges,
                'pk': whitelist.pk
            } for whitelist in Whitelist.objects.filter(**kwargs)]

            cache.set(key, json.dumps(cache_val), self.cache_timeout)
        else:
            cache_val = json.loads(cache_val)

        return [self.hydrate(item, lookup, value) for item in cache_val] 

    def make_cache_key(self, lookup, value):
        return 'whitelist:%s:%s' % (lookup, str(value))        

    def make_reverse_cache_key(self, item):
        return 'whitelist:%s' % str(item.pk)

    def hydrate(self, item, lookup, value):
        ranges = item.pop('ranges', [])
        item = self.model(**item)

        item.ranges = ranges

        key = self.make_reverse_cache_key(item)
        value = self.make_cache_key(lookup, value) 

        cache.set(key, value, self.cache_timeout)

        return item

class Whitelist(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __unicode__(self):
        return u'%s' % self.name

    def okay(self, ip, validate=netaddr.all_matching_cidrs):
        ranges = self.ranges[:]

        cidrs = ['%s/%d' % (whitelist_ip, cidr) for whitelist_ip, cidr in ranges]

        # if there are no associated ranges
        # with this whitelist, *do not fail*.
        if not len(cidrs):
            return True

        return len(validate(ip, cidrs)) > 0

    def get_ranges(self):
        return [[ip, cidr] for ip, cidr in self.range_set.values_list('ip', 'cidr')]

    def set_ranges(self, ranges=None):
        return []

    ranges = property(get_ranges, set_ranges)

class CachedWhitelist(Whitelist):
    objects = CachedWhitelistManager()

    _ranges = None 

    def get_ranges(self):
        if self._ranges is None:
            return super(CachedWhitelist, self).get_ranges()

        return self._ranges

    def set_ranges(self, ranges=None):
        self._ranges = ranges

    ranges = property(get_ranges, set_ranges)

    class Meta:
        proxy = True

class Range(models.Model):
    whitelist = models.ForeignKey(Whitelist)
    ip = models.IPAddressField()
    cidr = models.PositiveSmallIntegerField(default=32)

    def __unicode__(self):
        return u'%s/%d' % (self.ip, self.cidr)
