import functools

def exempt(view):
    @functools.wraps(view)
    def inner(*args, **kwargs):
        return view(*args, **kwargs)

    inner.mithril_exempt = True
    return inner

def resettable(reset_view):
    def outer(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            return fn(*args, **kwargs)

        inner.mithril_reset = reset_view
        return inner

    return outer
