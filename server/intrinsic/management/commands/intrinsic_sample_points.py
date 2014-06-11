from decimal import Decimal
from django.core.management.base import BaseCommand

from clint.textui import progress

from photos.models import Photo
from intrinsic.models import IntrinsicPoint
from intrinsic.tasks import sample_intrinsic_points_task


class Command(BaseCommand):
    args = ''
    help = 'Sample intrinsic points for all images'

    def handle(self, *args, **options):
        num_photos = int(args[1])

        #all_photos = Photo.objects \
            #.filter(scene_category_correct=True,
                    #scene_category_correct_score__isnull=False,
                    #stylized=False, nonperspective=False, rotated=False,
                    #whitebalanced=True, synthetic=False,
                    #license__publishable=True,
                    #num_intrinsic_comparisons__gt=0,
                    #median_intrinsic_error__isnull=False) \

        all_photos = Photo.objects \
            .filter(intrinsic_synthetic__multilayer_exr__isnull=False)

        all_photo_ids = all_photos \
            .order_by('num_intrinsic_comparisons') \
            .values_list('id', flat=True)

        kwargs = {}
        if args and args[0] == 'sparse':
            kwargs['min_separation'] = Decimal('0.07')
            kwargs['avoid_existing_points'] = True
            kwargs['chromaticity_thresh'] = 0.125
        elif args and args[0] == 'dense':
            kwargs['min_separation'] = Decimal('0.03')
            kwargs['avoid_existing_points'] = False
            kwargs['chromaticity_thresh'] = None
        else:
            print 'Usage: ./manage.py intrinsic_sample_points (sparse|dense)'
            return

        photo_ids = []
        for id in all_photo_ids:
            if (not IntrinsicPoint.objects.filter(
                    photo_id=id, min_separation=kwargs['min_separation']).exists()):
                photo_ids.append(id)
                if len(photo_ids) >= num_photos:
                    break

        print 'Queuing tasks on celery...'
        for photo_id in progress.bar(photo_ids):
            sample_intrinsic_points_task.delay(photo_id=photo_id, **kwargs)
