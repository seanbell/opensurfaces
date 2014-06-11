"""
.. describe:: ./manage.py mtconsume

    Dispatch all pending content to the marketplace and create new HITs.

    With our MTurk platform, tasks are dispatched in a two-step process.

    First, :class:`mturk.models.PendingContent` objects are created for each
    object that might be labeled (e.g. a photo).  ``PendingContent`` instances
    track the priority of each object, what has been scheduled, and how many
    tasks need to be put on MTurk.

    Second, ``mtconsume`` searches for ``PendingContent`` instances that have
    not yet been scheduled on MTurk (or that need more responses) and then
    creates HITs (stored locally as :class:`models.mturk.MtHit` instances).
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = ''
    help = 'Manually run an instance of consume_pending_objects_task'

    def handle(self, *args, **options):
        from mturk.tasks import consume_pending_objects_task
        consume_pending_objects_task(show_progress=True)
