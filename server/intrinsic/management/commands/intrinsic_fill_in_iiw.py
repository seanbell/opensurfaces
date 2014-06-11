from django.core.management.base import BaseCommand

from django.db.models import Q

from photos.models import Photo
from intrinsic.models import IntrinsicPointComparison


class Command(BaseCommand):
    args = ''
    help = 'Fix the point1_image_darker field'

    def handle(self, *args, **options):
        Photo.objects.all() \
            .update(in_iiw_dataset=False)

        Photo.objects \
            .filter(synthetic=False,
                    rotated=False,
                    nonperspective=False,
                    inappropriate=False,
                    stylized=False) \
            .filter(num_intrinsic_comparisons__gt=0) \
            .filter(Q(license__publishable=True) | Q(light_stack__isnull=False)) \
            .update(in_iiw_dataset=True)

        print 'iiw:', Photo.objects.filter(in_iiw_dataset=True).count()

        Photo.objects.all() \
            .update(in_iiw_dense_dataset=False)

        dense_photo_ids = IntrinsicPointComparison.objects \
            .filter(point1__min_separation__lt=0.05) \
            .order_by('photo') \
            .distinct('photo') \
            .values_list('photo_id', flat=True)

        Photo.objects \
            .filter(in_iiw_dataset=True) \
            .filter(id__in=dense_photo_ids) \
            .update(in_iiw_dense_dataset=True)

        print 'iiw dense:', Photo.objects.filter(in_iiw_dense_dataset=True).count()
