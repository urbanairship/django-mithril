# (c) 2012 Urban Airship and Contributors

def fake_settings(**kwargs):
    return type('FakeSettings', (object,), kwargs)()


def fmt_ip(ip_int):
    return '%d.%d.%d.%d' % (
        (ip_int & (0xFF << 24)) >> 24,
        (ip_int & (0xFF << 16)) >> 16,
        (ip_int & (0xFF <<  8)) >> 8,
        (ip_int & (0xFF))
    )
