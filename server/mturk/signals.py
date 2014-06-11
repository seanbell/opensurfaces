import django.dispatch

# sent when a HIT is expired
hit_expired = django.dispatch.Signal(providing_args=["instance"])
