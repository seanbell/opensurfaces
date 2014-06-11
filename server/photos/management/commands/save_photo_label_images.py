import os

from django.core.management.base import BaseCommand

from common.utils import queryset_progress_bar
from photos.models import Photo
from photos.tasks import download_photo_task, photo_to_label_image_task
from shapes.models import ShapeSubstance


class Command(BaseCommand):
    args = ''
    help = 'Exports photos'

    def handle(self, *args, **options):
        larger_dimension = 320
        local_dir = 'image-labels'

        COLORS = [
            (236,146,155),
            (127,0,134),
            (153,224,255),
            (185,244,105),
            (157,67,17),
            (252,45,68),
            (210,54,255),
            (0,136,160),
            (181,189,148),
            (255,204,180),
            (114,50,64),
            (195,204,255),
            (0,255,255),
            (122,141,0),
            (255,156,116),
            (161,0,59),
            (113,138,242),
            (0,221,164),
            (75,72,31),
            (131,116,111),
            (255,58,156),
            (0,76,237),
            (38,119,97),
            (244,211,0),
            (255,60,0),
            (242,200,232),
            (67,71,78),
            (0,133,29),
            (118,74,0),
            (255,140,250),
            (0,106,171),
            (0,248,9),
            (255,156,0),
            (114,64,115),
            (0,179,255),
            (193,201,189),
            (213,180,130)
        ]

        substance_names = [
            'Wood',
            'Painted',
            'Fabric/cloth',
            'Glass',
            'Metal',
            'Tile',
            'Carpet/rug',
            'Plastic - opaque',
            'Granite/marble',
            'Ceramic',
            'Paper/tissue',
            'Food',
            'Leather',
            'Plastic - clear',
            'Concrete',
            'Laminate',
            'Brick',
            'Mirror',
            'Cardboard',
            'Wallpaper',
            'Stone',
            'Wicker',
            'Skin',
            'Hair',
            'Rubber/latex',
            'Fur',
            'Foliage',
            'Wax',
            'Linoleum',
            'Sponge',
            'Sky',
            'Water',
            'Chalkboard/blackboard',
            'Cork/corkboard',
            'Fire',
        ]

        if len(COLORS) < len(substance_names):
            raise ValueError("too few colors")

        substance_to_id = dict(ShapeSubstance.objects
                               .filter(name__in=substance_names)
                               .values_list('name', 'id'))

        color_map = {substance_to_id[name]: COLORS[idx]
                     for idx, name in enumerate(substance_names)}

        with open('%s/Colors.txt' % local_dir, 'w') as f:
            for idx, name in enumerate(substance_names):
                c = COLORS[idx]
                print >>f, c[0], c[1], c[2], name

        print 'Names: %s' % substance_names
        print 'Name to ID: %s' % substance_to_id
        print 'Color map: %s' % color_map

        print 'Queueing tasks for download via celery...'
        qset = Photo.objects.filter(
            #scene_category__name='kitchen',
            #scene_category_correct=True,
            aspect_ratio__gte=0.5,
            aspect_ratio__lte=2.0,
        ).order_by('-num_vertices')#[:2000]

        for photo in queryset_progress_bar(qset):
            filename_base = os.path.abspath(os.path.join(
                local_dir, os.path.join('images', str(photo.id))))

            photo_to_label_image_task.delay(
                photo_id=photo.id,
                color_map=color_map,
                filename=filename_base + '_GT.png',
                format='PNG',
                next_task=download_photo_task.s(
                    photo_id=photo.id,
                    filename=filename_base + '.png',
                    format='PNG',
                    larger_dimension=larger_dimension)
            )
