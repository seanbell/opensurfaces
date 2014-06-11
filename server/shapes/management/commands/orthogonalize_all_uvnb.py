from django.core.management.base import BaseCommand
from clint.textui import progress

from normals.models import ShapeRectifiedNormalLabel
from normals.tasks import orthogonalize_rectified_normal


class Command(BaseCommand):
    args = ''
    help = 'Orthogonalize all rectified shapes'

    def handle(self, *args, **options):
        for id in progress.bar(ShapeRectifiedNormalLabel.objects.values_list('id', flat=True)):
            orthogonalize_rectified_normal.delay(id)
