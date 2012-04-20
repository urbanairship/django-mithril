# (c) 2012 Urban Airship and Contributors

import functools


def exempt(view):
    view.mithril_exempt = True
    return view


def resettable(reset_view):
    def outer(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            return fn(*args, **kwargs)

        inner.mithril_reset = reset_view
        return inner

    return outer
