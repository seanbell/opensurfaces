"""
.. describe:: ./manage.py mtcubam

    Update all labels for the experiments that use CUBAM to aggregate binary
    answers.  Since CUBAM is expensive and can take hours to run if you have
    millions of labels, it only runs on experiments thar are marked as "dirty".

    To force a re-run, mark the corresponding :class:`mturk.models.Experiment`
    instance to be dirty by running the following in a Python shell (you can
    start one with ``./manage.py shell_plus``):

    .. code-block:: py

        Experiment.objects.filter(slug='SLUG').update(cubam_dirty=True)

    where ``SLUG`` is the human-readable ID for your project.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = ''
    help = 'Updates labels using the CUBAM library'

    def handle(self, *args, **options):
        from mturk.tasks import mturk_update_votes_cubam_task
        mturk_update_votes_cubam_task(show_progress=True)
