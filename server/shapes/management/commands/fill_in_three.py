from clint.textui import progress

from django.core.management.base import BaseCommand
from django.db import transaction

from shapes.models import MaterialShape
from shapes.utils import update_shape_three


class Command(BaseCommand):
    args = ''
    help = 'Updates the three_js and three_bin attributes of material shapes'

    def handle(self, *args, **options):
        #with transaction.atomic():
        for p in progress.bar(MaterialShape.objects.all()):
            update_shape_three(p, save=True)
