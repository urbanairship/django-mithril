from django.db import models
import netaddr

class Whitelist(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __unicode__(self):
        return u'%s' % self.name

    def okay(self, ip):
        cidrs = ['%s/%d' % _range for _range in self.range_set.values_list('ip', 'cidr')] 
        return len(netaddr.all_matching_cidrs(ip, cidrs)) > 0

class Range(models.Model):
    whitelist = models.ForeignKey(Whitelist)
    ip = models.IPAddressField()
    cidr = models.PositiveSmallIntegerField(default=32)

    def __unicode__(self):
        return u'%s/%d' % (self.ip, self.cidr)
