# (c) 2012 Urban Airship and Contributors

from django.test import TestCase

from mithril.decorators import exempt, resettable

import random


class TestOfMithrilDecorators(TestCase):

    def test_exempt_attaches_appropriate_flag(self):
        anything = lambda *a: a
        expected = random.randint(0, 10)

        anything = exempt(anything)

        self.assertTrue(anything.mithril_exempt)

        self.assertEqual(anything(expected), (expected,))

    def test_resettable_attaches_arg_to_fn(self):
        anything = lambda *a: a
        expected = random.randint(0, 10)

        anything = resettable(expected)(anything)

        self.assertEqual(anything.mithril_reset, expected)
        self.assertEqual(anything(expected), (expected,))
