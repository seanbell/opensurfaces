"""
.. describe:: ./manage.py mtpending

    Search for any objects not described by an instance of
    :class:`mturk.models.PendingContent` and create ``PendingContent``
    instances.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = ''  # '<dir1> <dir2> ...'
    help = 'Scans for pending objects'

    def handle(self, *args, **options):
        from mturk.tasks import scan_all_for_pending_objects_task
        scan_all_for_pending_objects_task(show_progress=True)
