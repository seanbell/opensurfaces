from django.core.management.base import BaseCommand

from photos.models import Photo
from django.db.models import Q


class Command(BaseCommand):
    args = ''
    help = 'Generate LaTeX Supplemental Material visual comparisons'

    def handle(self, *args, **options):
        names = Photo.objects \
            .filter(stylized=False, num_intrinsic_comparisons__gt=0) \
            .filter(Q(license__publishable=True) | Q(light_stack__isnull=False)) \
            .filter(flickr_user__isnull=False) \
            .order_by() \
            .distinct('flickr_user') \
            .values_list('flickr_user__username', flat=True)
        print ' '.join(sorted(names))
