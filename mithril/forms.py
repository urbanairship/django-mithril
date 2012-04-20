from django import forms
from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from mithril.models import Whitelist
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
        formset_class = self.build_formset_class(
            kwargs.pop('range_form_class', None) or self.range_form_class
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
        return super(WhitelistForm, self).is_valid() and self.formset.is_valid()

    def clean(self, *args, **kwargs):
        retval = super(WhitelistForm, self).clean(*args, **kwargs)
        if self.cleaned_data.get('name', None) is not None:
            self.cleaned_data['slug'] = slugify(self.cleaned_data['name'])
        return retval

    def save(self):
        data = {
            'name':self.cleaned_data['name'],
            'slug':self.cleaned_data['slug'],
        }

        if not self.whitelist:
            self.whitelist = self.whitelist_class(**data)
            self.whitelist.save()
        else:
            type(self.whitelist).objects.filter(pk=self.whitelist.pk).update(**data)

        self.whitelist.range_set.all().delete()

        for form in self.formset.forms:
            if form in self.formset.deleted_forms:
                continue

            form_data = {
                'ip':form.cleaned_data['ip'],
                'cidr':form.cleaned_data['cidr'], 
            }
          
            self.whitelist.range_set.create(**form_data)

        return self.whitelist

