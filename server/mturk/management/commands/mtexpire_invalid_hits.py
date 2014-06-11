from clint.textui import progress

from django.core.management.base import BaseCommand
from django.db import transaction

from mturk.models import MtHit


class Command(BaseCommand):
    args = ''
    help = 'Fixes a bug with objects being sent out early'

    def handle(self, *args, **options):
        from mturk.tasks import expire_invalid_hits
        expire_invalid_hits(show_progress=True)
