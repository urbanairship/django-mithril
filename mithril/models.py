from django.db import models

class Whitelist(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __unicode__(self):
        return u'%s' % self.name

    def okay(self, ip):
        pass

class Range(models.Model):
    ip = models.IPAddressField()
    cidr = models.PositiveSmallIntegerField(default=32)

    def __unicode__(self):
        return u'%s/%d' % (self.ip, self.cidr)

    def okay(self, ip):
        pass
