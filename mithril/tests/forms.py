# (c) 2012 Urban Airship and Contributors

from django.test import TestCase
from django.template.defaultfilters import slugify
from mithril.forms import WhitelistForm, RangeForm
from mithril.models import Whitelist
from mithril.tests.utils import fmt_ip
from django import forms
import random

class MithrilFormsTestCase(TestCase):
    def test_allows_custom_range_form_class(self):
        class CustomRangeForm(RangeForm):
            pass

        wlf = WhitelistForm(None, None, range_form_class=CustomRangeForm)
        self.assertEqual(wlf.formset.form, CustomRangeForm)

    def test_defaults_to_classes_range_form_class(self):
        class CustomRangeForm(RangeForm):
            pass

        class CustomWhitelistForm(WhitelistForm):
            range_form_class = CustomRangeForm

        wlf = CustomWhitelistForm(None, None, range_form_class=CustomRangeForm)
        self.assertEqual(wlf.formset.form, CustomRangeForm)

    def test_sets_current_ip_initial_data(self):
        Expected = object()

        wlf = WhitelistForm(Expected, None)
        self.assertEqual(wlf.initial['current_ip'], Expected)

    def test_sets_current_name_to_whitelist_name(self):
        Expected = 'random'

        wl = Whitelist.objects.create(
            name=Expected,
            slug='lolwat'
        )

        wlf = WhitelistForm(None, wl)
        self.assertEqual(wlf.initial['name'], Expected)

    def test_build_formset_creates_initial_data_if_whitelist_is_present(self):
        num_ranges = random.randint(1, 10)
        wl = Whitelist.objects.create(
            name='anything',
            slug='anything',
        )

        l = []
        for i in range(num_ranges):
            r = wl.range_set.create(
                ip=fmt_ip(random.randint(0, 0xFFFFFFFF)),
                cidr=random.randint(0, 32)
            )
            l.append(r)

        wlf = WhitelistForm(None, wl)
        self.assertEqual(len(wlf.formset.initial), num_ranges)

        for idx, initial in enumerate(wlf.formset.initial):
            self.assertEqual(
                initial['ip'], l[idx].ip
            )
            self.assertEqual(
                initial['cidr'], l[idx].cidr
            )

    def test_build_formset_sets_appropriate_prefix(self):
        prefix = 'random-%d' % random.randint(0, 10)
        wlf = WhitelistForm(None, prefix=prefix)

        self.assertEqual(wlf.formset.prefix, '%s_formset' % prefix)

    def test_is_valid_validates_formset(self):

        data = {
            'name':'x',
            'current_ip':'x',
            '_formset-TOTAL_FORMS':'0',
            '_formset-INITIAL_FORMS':'0',
            '_formset-MAX_FORMS':'0',
        }
        wlf = WhitelistForm(None, None, data)
        wlf.formset = type('X', (object,), {'is_valid':lambda *a: True})()
        self.assertTrue(wlf.is_valid())

        wlf = WhitelistForm(None, None, data)
        wlf.formset = type('X', (object,), {'is_valid':lambda *a: False})()
        self.assertFalse(wlf.is_valid())
        

    def test_clean_sets_slug_to_slugified_name(self):
        name = ' '.join([str(random.randint(0, 10)) for i in range(10)])
        data = {
            'name':name,
            'current_ip':'x',
            '_formset-TOTAL_FORMS':'0',
            '_formset-INITIAL_FORMS':'0',
            '_formset-MAX_FORMS':'0',
        }
        wlf = WhitelistForm(None, None, data)
        wlf.is_valid()
        self.assertEqual(wlf.cleaned_data['slug'], slugify(name)) 

    def test_save_sets_appropriate_ranges(self):
        num_forms = random.randint(1, 10)
        name = ' '.join([str(random.randint(0, 10)) for i in range(10)])
        data = {
            'name':name,
            'current_ip':'x',
            '_formset-TOTAL_FORMS':'%d' % num_forms,
            '_formset-INITIAL_FORMS':'0',
            '_formset-MAX_FORMS':'',
        }

        for i in range(num_forms):
            data['_formset-%d-ip' % i] = fmt_ip(random.randint(0, 0xFFFFFFFF))
            data['_formset-%d-cidr' % i] = random.randint(0, 32)
    
        wlf = WhitelistForm(None, None, data)

        wlf.is_valid()

        self.assertTrue(wlf.is_valid())
        
        wl = wlf.save()

        for i in range(num_forms):
            self.assertTrue(wl.range_set.filter(
                ip=data['_formset-%d-ip' % i],
                cidr=data['_formset-%d-cidr' % i]
            ).exists())

    def test_save_sets_appropriate_field_values(self):
        name = ' '.join([str(random.randint(0, 10)) for i in range(10)])
        data = {
            'name':name,
            'current_ip':'x',
            '_formset-TOTAL_FORMS':'0',
            '_formset-INITIAL_FORMS':'0',
            '_formset-MAX_FORMS':'0',
        }
        wl = Whitelist.objects.create(
            name='asdf',
            slug='asdf',
        )
        wlf = WhitelistForm(None, wl, data)
        wlf.is_valid()
        wlf.save()

        wl = Whitelist.objects.get(pk=wl.pk)

        self.assertEqual(wl.name, name)
        self.assertEqual(wl.slug, slugify(name))

    def test_save_returns_created_whitelist(self):
        name = ' '.join([str(random.randint(0, 10)) for i in range(10)])
        data = {
            'name':name,
            'current_ip':'x',
            '_formset-TOTAL_FORMS':'0',
            '_formset-INITIAL_FORMS':'0',
            '_formset-MAX_FORMS':'0',
        }
        wl = Whitelist.objects.create(
            name='asdf',
            slug='asdf',
        )
        wlf = WhitelistForm(None, wl, data)
        wlf.is_valid()
        self.assertEqual(wlf.save().pk, wl.pk)
