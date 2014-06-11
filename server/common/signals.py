import django.dispatch

# sent when a worker submission is invalidated by an admin user
marked_invalid = django.dispatch.Signal(providing_args=["instance"])
