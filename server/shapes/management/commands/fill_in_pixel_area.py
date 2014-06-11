from clint.textui import progress

from django.core.management.base import BaseCommand

from shapes.models import MaterialShape


class Command(BaseCommand):
    args = ''
    help = 'Helper to fill in the potentially empty pixel_area field'

    def handle(self, *args, **options):
        #with transaction.atomic():
        for shape in progress.bar(MaterialShape.objects.all()):
            shape.pixel_area = shape.area_pixels()
            shape.save()
