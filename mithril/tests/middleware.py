# (c) 2012 Urban Airship and Contributors

from django.test import TestCase
from mithril.tests.utils import fake_settings
from mithril.tests.fake_strategy import FakeStrategy
from mithril.middleware import WhitelistMiddleware
import random
import mithril

class RaisesAttributeError(WhitelistMiddleware):
    def get_strategy(*a, **kw):
        raise AttributeError() 

class MiddlewareTestCase(TestCase):
    def test_get_strategy(self):
        settings = fake_settings(
            MITHRIL_STRATEGY='mithril.tests.fake_strategy.FakeStrategy'
        )

        middleware = WhitelistMiddleware()
        strategy = middleware.get_strategy(settings)
        self.assertTrue(isinstance(strategy, FakeStrategy)) 

    def test_process_request_swallows_attribute_error(self):
        mw = RaisesAttributeError()
        self.assertEqual(mw.process_request(random.randint(0, 10)), None)

    def test_process_request_calls_set_ip(self):
        self.assertEqual(mithril.get_current_ip(), None)
        expected = '%d.%d.%d.%d' % tuple([random.randint(1, 254)] * 4)
        with self.settings(MIDDLEWARE_CLASSES=['mithril.middleware.WhitelistMiddleware'], MITHRIL_STRATEGY='mithril.tests.fake_strategy.FakeStrategy'):
            try:
                self.client.get('/', REMOTE_ADDR=expected)
            except:
                pass

            self.assertEqual(mithril.get_current_ip(), expected)

    def test_process_view_skips_exempt(self):
        anything = lambda *a: a
        anything.mithril_exempt = True
        mw = WhitelistMiddleware()

        self.assertEqual(
            mw.process_view(None, anything, None, None),
            None
        )

    def test_process_view_swallows_attribute_error(self):
        mw = RaisesAttributeError()
        self.assertEqual(mw.process_view(random.randint(0, 10), random.randint(0, 10), random.randint(0, 10), random.randint(0, 10)), None)

    def test_process_view_delegates_to_strategy(self):
        strategy = FakeStrategy()
        expected = random.randint(0, 10)

        def collect(*a, **kw):
            strategy.args = a
            strategy.kwargs = kw
            return expected

        strategy.process_view = collect

        mw = WhitelistMiddleware()
        mw.get_strategy = lambda *a: strategy

        result = mw.process_view(expected, expected, [], {})

        self.assertEqual(result, expected)
        self.assertEqual(strategy.args, (expected, expected))
        self.assertEqual(strategy.kwargs, {})



