from clint.textui import progress

from django.core.management.base import BaseCommand

from shapes.models import MaterialShape
from shapes.utils import rectify_shape


class Command(BaseCommand):
    args = ''
    help = 'Rectify all shapes'

    def handle(self, *args, **options):
        #print ('This will recompute the rectified image on all shapes')

        #if raw_input("Are you sure? [y/n] ").lower() != "y":
            #print 'Exiting'
            #return

        print ('Recomputing the rectified image for all shapes')

        shapes = MaterialShape.objects \
            .filter(planar=True, planar_score__isnull=False) \
            .order_by('-planar_score', '-area')

        # delete existing rectified image
        print 'deleting old rectified textures'
        for shape in progress.bar(shapes):
            if shape.image_rectified:
                shape.image_rectified.delete(save=True)
            if shape.thumb_rectified_span3:
                shape.thumb_rectified_span3.delete(save=True)

        print 'computing new rectified textures'
        for shape in progress.bar(shapes):
            if shape.normals.count() < 1:
                continue

            print ''
            rectify_shape(shape)
            print ''
