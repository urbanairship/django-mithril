import django


def pre_django_1_9():
    return django.__version__[0] == 1 and django.__version__[1] < 9
