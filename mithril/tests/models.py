from django.test import TestCase
from mithril.models import Whitelist
from mithril.tests.utils import fmt_ip
import random
import netaddr


class WhitelistTestCase(TestCase):
    def test_netaddr_integration(self):
        # just a tiny range, here
        test_ip = random.randint(0, 0xFFFFFFFF)
        num_ranges = random.randint(0, 10)

        whitelist = Whitelist.objects.create(
            name='anything',
            slug='anything'
        )
        cidrs = []

        for idx in range(num_ranges): 
            r = whitelist.range_set.create(
                ip = fmt_ip(random.randint(0, 0xFFFFFFFF)),
                cidr = random.randint(1, 32) 
            )
            cidrs.append('%s/%d' % (r.ip, r.cidr))
    
        self.assertEqual(
            whitelist.okay(test_ip),
            len(netaddr.all_matching_cidrs(test_ip, cidrs)) > 0
        )
 
