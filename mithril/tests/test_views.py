# (c) 2012 Urban Airship and Contributors
import django
from django.test import TestCase
from django.views.decorators.csrf import csrf_exempt

from mithril.models import Whitelist
from mithril.views import WhitelistEditor
from mithril.utils import pre_django_1_9

import os

Expected = object()

def test_context_processor(request):
    return {
        'expected': Expected
    }

class ViewDispatch(object):
    view = None

    def __call__(self, *args, **kwargs):
        return self.view(*args, **kwargs)

if pre_django_1_9():
    from django.conf.urls import patterns
    urlpatterns = patterns('',
        ('^', csrf_exempt(ViewDispatch())),
    )
    REDIRECT_URL = 'http://testserver/'
else:
    from django.conf.urls import url
    urlpatterns = [
        url('^', csrf_exempt(ViewDispatch())),
    ]
    REDIRECT_URL = '.'

class MithrilViewTestCase(TestCase):
    test_settings = {
        'TEMPLATE_LOADERS': ('django.template.loaders.filesystem.Loader',),
        'TEMPLATE_DIRS': (os.path.join(os.path.dirname(__file__), 'templates'),),
        'TEMPLATE_CONTEXT_PROCESSORS': ('mithril.tests.test_views.test_context_processor',),
        'MITHRIL_STRATEGY': 'mithril.tests.fake_strategy.FakeStrategy',
        'ROOT_URLCONF': 'mithril.tests.test_views',
    }

    def test_view_returns_form_and_whitelist_on_get(self):
        wl = Whitelist.objects.create(name='anything', slug='anything')

        ViewDispatch.view = WhitelistEditor(lambda *a: wl)

        with self.settings(**self.test_settings):
            resp = self.client.get('/')
            self.assertTrue('form' in resp.context)
            self.assertTrue('whitelist' in resp.context)

            self.assertEqual(resp.context['whitelist'], wl)
            self.assertTrue(isinstance(resp.context['form'], WhitelistEditor.form_class))

    def test_view_allows_custom_form_class(self):
        wl = Whitelist.objects.create(name='anything', slug='anything')

        custom_form_class = type('CustomForm', (WhitelistEditor.form_class,), {})

        ViewDispatch.view = WhitelistEditor(lambda *a: wl)
        ViewDispatch.view.form_class = custom_form_class
        with self.settings(**self.test_settings):
            resp = self.client.get('/')
            self.assertTrue(isinstance(resp.context['form'], custom_form_class))

    def test_has_request_context_processor_data(self):
        wl = Whitelist.objects.create(name='anything', slug='anything')

        ViewDispatch.view = WhitelistEditor(lambda *a: wl)

        with self.settings(**self.test_settings):
            resp = self.client.get('/')
            import pdb; pdb.set_trace()
            self.assertEqual(resp.context['expected'], Expected)

    def test_view_allows_custom_template(self):
        wl = Whitelist.objects.create(name='anything', slug='anything')

        ViewDispatch.view = WhitelistEditor(lambda *a: wl)
        ViewDispatch.view.template = 'mithril/whitelist_edit_custom.html'

        with self.settings(**self.test_settings):
            resp = self.client.get('/')
            self.assertEqual(resp.templates[0].name, ViewDispatch.view.template)

    def test_view_returns_form_with_errors_on_bad_post(self):
        wl = Whitelist.objects.create(name='anything', slug='anything')

        ViewDispatch.view = WhitelistEditor(lambda *a: wl)

        formset = WhitelistEditor.form_class(None, None).formset
        formset_data = formset.management_form.initial
        data = dict([
            ('%s-%s' % (formset.prefix, key), value if value is not None else '')
            for key, value
            in formset_data.iteritems()
        ])

        with self.settings(**self.test_settings):
            resp = self.client.post('/', data)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(len(resp.context['form'].errors))

    def test_view_returns_redirect_on_valid_form(self):
        wl = Whitelist.objects.create(name='anything', slug='anything')

        ViewDispatch.view = WhitelistEditor(lambda *a: wl)

        formset = WhitelistEditor.form_class(None, None).formset
        formset_data = formset.management_form.initial
        data = dict([
            ('%s-%s' % (formset.prefix, key), value if value is not None else '')
            for key, value
            in formset_data.iteritems()
        ])
        data['name'] = 'random'
        data['current_ip'] = '0.0.0.0'

        with self.settings(**self.test_settings):
            resp = self.client.post('/', data)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp['Location'], REDIRECT_URL)

    def test_view_creates_new_whitelist_on_valid_form(self):
        ViewDispatch.view = WhitelistEditor(lambda *a: None)

        formset = WhitelistEditor.form_class(None, None).formset
        formset_data = formset.management_form.initial
        data = dict([
            ('%s-%s' % (formset.prefix, key), value if value is not None else '')
            for key, value
            in formset_data.iteritems()
        ])
        data['name'] = 'random'
        data['current_ip'] = '0.0.0.0'

        num_whitelists = len(Whitelist.objects.all())

        with self.settings(**self.test_settings):
            resp = self.client.post('/', data)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp['Location'], REDIRECT_URL)
            self.assertEqual(len(Whitelist.objects.all()), num_whitelists+1)

    def test_view_updates_existing_whitelist_on_valid_form(self):
        wl = Whitelist.objects.create(name='anything', slug='anything')
        ViewDispatch.view = WhitelistEditor(lambda *a: wl)

        formset = WhitelistEditor.form_class(None, None).formset
        formset_data = formset.management_form.initial
        data = dict([
            ('%s-%s' % (formset.prefix, key), value if value is not None else '')
            for key, value
            in formset_data.iteritems()
        ])
        data['name'] = 'random'
        data['current_ip'] = '0.0.0.0'

        num_whitelists = len(Whitelist.objects.all())

        with self.settings(**self.test_settings):
            resp = self.client.post('/', data)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp['Location'], REDIRECT_URL)
            self.assertEqual(len(Whitelist.objects.all()), num_whitelists)

            new_wl = Whitelist.objects.get(pk=wl.pk)
            self.assertEqual(new_wl.name, 'random')
            self.assertEqual(new_wl.slug, 'random')

