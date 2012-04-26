# (c) 2012 Urban Airship and Contributors

from django.db import models
import netaddr

class Whitelist(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __unicode__(self):
        return u'%s' % self.name

    def okay(self, ip, validate=netaddr.all_matching_cidrs):
        cidrs = ['%s/%d' % _range for _range in self.range_set.values_list('ip', 'cidr')] 

        # if there are no associated ranges
        # with this whitelist, *do not fail*.
        if not len(cidrs):
            return True

        return len(validate(ip, cidrs)) > 0

class Range(models.Model):
    whitelist = models.ForeignKey(Whitelist)
    ip = models.IPAddressField()
    cidr = models.PositiveSmallIntegerField(default=32)

    def __unicode__(self):
        return u'%s/%d' % (self.ip, self.cidr)
