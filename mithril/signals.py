import django.dispatch

user_login_failed = django.dispatch.Signal(providing_args=['partial_credentials', 'ip'])
user_view_failed = django.dispatch.Signal(providing_args=['user', 'url', 'ip'])
