# (c) 2012 Urban Airship and Contributors

from django import forms
from django.core.cache import cache
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from mithril.models import Whitelist, CachedWhitelistManager
import netaddr


class RangeForm(forms.Form):
    ip = forms.IPAddressField()
    cidr = forms.IntegerField(min_value=0, max_value=32)

    def clean(self):
        ret_value = super(RangeForm, self).clean()

        if 'ip' not in self.cleaned_data or 'cidr' not in self.cleaned_data:
            return

        ip_cidr = '%s/%s' % (self.cleaned_data['ip'], self.cleaned_data['cidr'])

        try:
            netaddr.ip.IPNetwork(ip_cidr) 
        except (ValueError, netaddr.ip.AddrFormatError), e:
            raise forms.ValidationError('%s is not a valid IP/CIDR combination' % ip_cidr)

        return ret_value


class WhitelistForm(forms.Form):

    range_form_class = RangeForm
    whitelist_class = Whitelist

    name = forms.CharField()
    current_ip = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, current_ip, whitelist=None, *args, **kwargs):
        self.whitelist = whitelist
        self._current_ip = current_ip
        formset_class = self.build_formset_class(
            kwargs.pop('range_form_class', self.range_form_class)
        )

        extend_initial = {'current_ip':current_ip}
        if self.whitelist:
            extend_initial['name'] = self.whitelist.name

        kwargs['initial'] = dict(kwargs.get('initial', {}), **extend_initial)

        self.formset = self.build_formset(formset_class, *args, **kwargs)

        super(WhitelistForm, self).__init__(*args, **kwargs)

    def build_formset_class(self, base_class):
        return formset_factory(base_class, extra=0, can_delete=True)

    def build_formset(self, formset_class, *args, **kwargs):
        formset_kwargs = {}
        formset_kwargs.update(kwargs)

        prefix = '%s_formset' % kwargs.get('prefix', '')

        formset_kwargs.pop('initial', None)
        if self.whitelist:
            formset_kwargs['initial'] = self.whitelist.range_set.values('ip', 'cidr')

        formset_kwargs['prefix'] = prefix

        return formset_class(*args, **formset_kwargs)

    def is_valid(self):
        return self.formset.is_valid() and super(
                WhitelistForm, self).is_valid()

    def clean(self, *args, **kwargs):
        retval = super(WhitelistForm, self).clean(*args, **kwargs)
        if self.cleaned_data.get('name', None) is not None:
            self.cleaned_data['slug'] = slugify(self.cleaned_data['name'])

        if not self.formset.is_valid():
            return

        cidr_ips = []
        has_deleted_forms = hasattr(self.formset, 'deleted_forms')
        for form in self.formset.forms:
            if has_deleted_forms and form in self.formset.deleted_forms:
                continue

            cidr_ips.append('%(ip)s/%(cidr)s' % (form.cleaned_data))

        if self._current_ip and cidr_ips:
            ips = netaddr.all_matching_cidrs(self._current_ip, cidr_ips)
            if not ips:
                raise forms.ValidationError(
                        'These settings would blacklist your current IP.')

        return retval

    def destroy_cache(self, whitelist):
        cwm = CachedWhitelistManager()

        cwm.clear_cache_for(whitelist)
        reverse_key = cwm.make_reverse_cache_key(whitelist)
        reverse_value = cache.get(reverse_key)

        if reverse_value:
            cache.delete(reverse_value)

    def save(self):
        data = {
            'name': self.cleaned_data['name'],
            'slug': self.cleaned_data['slug'],
        }

        if not self.whitelist:
            self.whitelist = self.whitelist_class(**data)
            self.whitelist.save()
        else:
            type(self.whitelist).objects.filter(
                    pk=self.whitelist.pk).update(**data)

        self.whitelist.range_set.all().delete()

        for form in self.formset.forms:
            if form in self.formset.deleted_forms:
                continue

            form_data = {
                'ip':form.cleaned_data['ip'],
                'cidr':form.cleaned_data['cidr'], 
            }
            self.whitelist.range_set.create(**form_data)

        self.destroy_cache(self.whitelist)

        return self.whitelist

