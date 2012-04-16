import functools

def mithril_exempt(view):
    @functools.wraps(view)
    def inner(request, *args, **kwargs):
        return view(*args, **kwargs)

    inner.mithril_exempt = True
    return inner
