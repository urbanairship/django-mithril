from django.contrib import admin
from mithril import models
from django.conf import settings


class RangeInline(admin.TabularInline):
    model = models.Range


class WhitelistAdmin(admin.ModelAdmin):
    inlines = [RangeInline]


if getattr(settings, 'MITHRIL_ADMIN_ENABLED', True):
    admin.site.register(models.Whitelist, WhitelistAdmin)
