from clint.textui import progress

from django.core.management.base import BaseCommand

from photos.models import Photo
from photos.tasks import detect_vanishing_points


class Command(BaseCommand):
    args = ''
    help = 'Detect vanishing points for all images'

    def handle(self, *args, **options):

        qset = Photo.objects.filter(vanishing_points='') \
                .order_by('-scene_category_correct_score') \
                .values_list('id', flat=True)

        for id in progress.bar(qset):
            detect_vanishing_points.delay(id)
