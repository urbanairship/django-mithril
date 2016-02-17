# (c) 2012 Urban Airship and Contributors

__version__ = (0, 2, 0)

class RequestIPStorage(object):
    def __init__(self):
        self.ip = None

    def set(self, ip):
        self.ip = ip

    def get(self):
        return self.ip

_request_ip_storage = RequestIPStorage()

get_current_ip = _request_ip_storage.get
set_current_ip = _request_ip_storage.set
