from clint.textui import progress

from django.core.management.base import BaseCommand
from django.db.models import Count

from shapes.models import MaterialShape
from normals.tasks import auto_rectify_shape


class Command(BaseCommand):
    args = ''
    help = 'Auto-rectify all shapes'

    def handle(self, *args, **options):

        ids = MaterialShape.objects.filter(correct=True, planar=True) \
            .exclude(rectified_normal__automatic=True) \
            .filter(rectified_normals__automatic=False) \
            .annotate(c=Count('rectified_normals')) \
            .filter(c__gt=0) \
            .order_by('-num_vertices') \
            .values_list('id', flat=True)

        for id in progress.bar(ids):
            auto_rectify_shape.delay(id)
