from django.core.management.base import BaseCommand

from common.utils import queryset_progress_bar
from shapes.models import MaterialShape
from shapes.tasks import create_shape_image_sample_task


class Command(BaseCommand):
    args = ""
    help = "Obtain a square image sampe for different material types"

    def handle(self, *args, **options):
        qset = MaterialShape.objects.filter(
            correct=True,
            substance__isnull=False,
            substance__fail=False).order_by('-area')
        for shape in queryset_progress_bar(qset):
            create_shape_image_sample_task.delay(
                shape, sample_width=256, sample_height=256)
