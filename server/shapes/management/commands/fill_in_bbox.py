from clint.textui import progress

from django.core.management.base import BaseCommand

from shapes.models import MaterialShape
from shapes.tasks import fill_in_bbox_task


class Command(BaseCommand):
    args = ''
    help = 'Helper to fill in the potentially empty image_bbox field'

    def handle(self, *args, **options):
        #with transaction.atomic():
        for shape in progress.bar(MaterialShape.objects.all().iterator(), expected_size=MaterialShape.objects.count()):
            fill_in_bbox_task.delay(shape)
