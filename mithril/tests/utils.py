# (c) 2012 Urban Airship and Contributors

def fake_settings(**kwargs):
    return type('FakeSettings', (object,), kwargs)()


def fmt_ip(ip_int):
    """
        ``ip_int`` is a 32-bit integer representing an IP with octets A.B.C.D
        arranged like so::

            A << 24 | B << 16 | C << 8 | D

        returns the number formatted as an IP address string.
    """
    return '%d.%d.%d.%d' % (
        (ip_int & (0xFF << 24)) >> 24,
        (ip_int & (0xFF << 16)) >> 16,
        (ip_int & (0xFF <<  8)) >> 8,
        (ip_int & (0xFF))
    )
