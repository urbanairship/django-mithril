# (c) 2012 Urban Airship and Contributors
import netaddr
import simplejson as json

from django.db import models
from django.conf import settings
from django.core.cache import cache


class CachedWhitelistManager(models.Manager):
    """
        Interface for the CachedWhitelist.

        Performs cache checks on ``filter``, and provides
        a mechanism for cache invalidation on a per
        ``Whitelist`` instance basis.

        The cache structure looks like so::

            * Lookup key: ``lookup:lookup_value`` -> serialized list of
              matched whitelists.

            * Reverse key: ``whitelist.pk`` -> list of lookup keys
              that apply to this whitelist.

        Example::

            wl = Whitelist.objects.create(name='lol', slug='lol')
            wl.range_set.create(ip='1.2.3.4', cidr=32)

            CachedWhitelist.objects.filter(pk=1)
            # which produces a lookup key: "whitelist:pk:1" that points to
            # [{"name":"lol", "pk":"1", "slug":"lol", "ranges":[["1.2.3.4", 32]]]

            # and a reverse key: "whitelist:1" that points to
            # ["whitelist:pk:1"]

    """
    cache_timeout = getattr(settings, 'MITHRIL_CACHE_TIMEOUT', 60 * 30)

    def create(self, **kwargs):
        super_create = super(CachedWhitelistManager, self).create

        obj = super_create(**kwargs)

        self.clear_cache_for(obj)

        return obj

    def filter(self, **kwargs):
        """
            Override base filter, and when a single lookup / value
            pair is detected, attempt to load from cache.

            When there's a cache miss, create a lookup key that
            points to serialized representation of all of the matched
            whitelists.

            For each of the matched whitelists, generate a reverse lookup
            key (from Whitelist to a list of lookup keys) and store that
            in the cache.
        """
        super_filter = super(CachedWhitelistManager, self).filter

        try:
            [(lookup, value)] = kwargs.items()
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

    def hydrate(self, data, lookup, value):
        """
            Given encoded JSON data representing a whitelist and its
            ranges, and the lookup and value that yielded that whitelist,
            recreate the whitelist as a full-fledged model instance.

            Additionally, store a reverse key to the lookup and value that
            created this whitelist (for cache invalidation.)
        """
        ranges = data.pop('ranges', [])
        item = self.model(**data)

        item.ranges = ranges

        cache_key = self.make_cache_key(lookup, value)

        self.store_reverse_cache(item, cache_key)
        return item

    def store_reverse_cache(self, whitelist, lookup_key):
        """
            Given an item, and a ``lookup:value`` key, create
            a reverse key to allow us to invalid the cache for
            a given whitelist.
        """
        key = self.make_reverse_cache_key(whitelist)
        items = json.loads(cache.get(key) or "[]")
        items.append(lookup_key)
        cache.set(key, json.dumps(items), self.cache_timeout)

    def clear_cache_for(self, whitelist):
        """
            Given a whitelist, lookup all the ``lookup:value``
            keys that apply to that whitelist. Delete all of those
            reversed values, as well as the ``reverse_key``.
        """
        reverse_key = self.make_reverse_cache_key(whitelist)

        items = json.loads(cache.get(reverse_key) or "[]")
        cache.delete_many(items + [reverse_key])


class Whitelist(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField()

    def __unicode__(self):
        return u'%s' % self.name

    def okay(self, ip, validate=netaddr.all_matching_cidrs):
        """
            Given an IP address as a string, create a CIDR-style
            list of all of the ranges that apply to this Whitelist,
            and make sure that at least one range applies to the IP.

            If this whitelist includes *no* ranges (which is almost certainly
            a user error), return True. Otherwise, return True if at
            least one range applied to the given IP.
        """
        cidrs = ['%s/%d' % (whitelist_ip, cidr) for whitelist_ip, cidr in self.ranges]

        # if there are no associated ranges
        # with this whitelist, *do not fail*.
        if not len(cidrs):
            return True

        return len(validate(ip, cidrs)) > 0

    def _get_ranges(self):
        return [[ip, cidr] for ip, cidr in self.range_set.values_list('ip', 'cidr')]

    def _set_ranges(self, ranges=None):
        return []

    ranges = property(_get_ranges, _set_ranges)


class CachedWhitelist(Whitelist):
    objects = CachedWhitelistManager()

    _ranges = None

    def _get_ranges(self):
        if self._ranges is None:
            return super(CachedWhitelist, self)._get_ranges()

        return self._ranges

    def _set_ranges(self, ranges=None):
        self._ranges = ranges

    ranges = property(_get_ranges, _set_ranges)

    class Meta:
        proxy = True


class Range(models.Model):
    whitelist = models.ForeignKey(Whitelist)
    ip = models.GenericIPAddressField(db_index=True)
    cidr = models.PositiveSmallIntegerField(default=32, db_index=True)

    def __unicode__(self):
        return u'%s/%d' % (self.ip, self.cidr)
