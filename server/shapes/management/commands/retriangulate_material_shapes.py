from clint.textui import progress

from django.core.management.base import BaseCommand

from photos.models import Photo
from shapes.models import MaterialShape
from shapes.tasks import retriangulate_material_shapes_task


class Command(BaseCommand):
    args = ''
    help = 'Retriangulates all material shapes'

    def handle(self, *args, **options):
        print ('This will delete all material shapes, '
               'thereby deleting all quality votes and '
               'any derivative items')

        if raw_input("Are you sure? [y/n] ").lower() != "y":
            print 'Exiting'
            return

        if raw_input("Is it backed up? [y/n] ").lower() != "y":
            print 'Exiting'
            return

        # delete existing shapes
        for shape in progress.bar(MaterialShape.objects.all()):
            for f in shape._ik.spec_files:
                f.delete()
            shape.delete()

        # schedule new ones to be computed
        for photo in progress.bar(Photo.objects.all()):
            retriangulate_material_shapes_task.delay(photo)
