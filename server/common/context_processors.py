from django.conf import settings


def debug(context):
    """ Adds the DEBUG and ENABLE_CACHING variable to the context of all
    templates """
    return {
        'DEBUG': settings.DEBUG,
        'ENABLE_CACHING': settings.ENABLE_CACHING,
    }
