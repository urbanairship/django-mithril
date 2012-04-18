from django import forms
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from mithril.models import Whitelist
import netaddr

class RangeForm(forms.Form):
    ip = forms.IPAddressField()
    cidr = forms.IntegerField(min_value=0, max_value=32)

    def clean(self):
        super(RangeForm, self).clean()

        ip_cidr = '%s/%s' % (self.cleaned_data['ip'], self.cleaned_data['cidr'])

        try:
            netaddr.ip.IPNetwork(ip_cidr) 
        except (ValueError, netaddr.ip.AddrFormatError), e:
            raise forms.ValidationError('%s is not a valid IP/CIDR combination' % ip_cidr)


class WhitelistForm(forms.Form):
    range_form_class = RangeForm
    whitelist_class = Whitelist

    name = forms.CharField()
    current_ip = forms.CharField(widget=forms.HiddenInput)


    def __init__(self, current_ip, whitelist=None, *args, **kwargs):
        self.whitelist = whitelist
        formset_class = self.build_formset_class()

        kwargs['initial'] = dict(kwargs.get('initial', {}), current_ip=current_ip)

        self.formset = self.build_formset(formset_class, *args, **kwargs)

        super(WhitelistForm, self).__init__(*args, **kwargs)

    def build_formset_class(self):
        return formset_factory(self.range_form_class, extra=1)
    
    def build_formset(self, formset_class, *args, **kwargs):
        formset_kwargs = {}
        formset_kwargs.update(kwargs)

        prefix = '%s_formset' % kwargs.get('prefix', '')
        formset_kwargs['initial'] = self.whitelist.range_set.values('ip', 'cidr')

        return formset_class(*args, **formset_kwargs)

    def is_valid(self):
        return super(WhitelistForm, self).is_valid() and self.formset.is_valid()

    def clean(self, *args, **kwargs):
        retval = super(WhitelistForm, self).clean(*args, **kwargs)
        self.cleaned_data['slug'] = slugify(self.cleaned_data['name'])
        return retval

    def save(self):
        if not self.whitelist:
            self.whitelist = self.whitelist_class(**self.cleaned_data)
            self.whitelist.save()
        else:
            type(self.whitelist).objects.filter(pk=self.whitelist.pk).update(**self.cleaned_data)

        self.whitelist.range_set.all().delete()
        
        if hasattr(self.whitelist.range_set, 'bulk_create'):
            self.whitelist.range_set.bulk_create([
                self.whitelist.range_set.model(**item)
                for item in self.formset_cleaned_data
            ])
        else:
            [self.whitelist.range_set.create(**item) for item in self.formset.cleaned_data]

        return self.whitelist

