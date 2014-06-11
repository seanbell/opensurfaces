from django.core.management.base import BaseCommand

from common.utils import progress_bar
from intrinsic.models import IntrinsicImagesDecomposition
from intrinsic.tasks import upload_intrinsic_file


class Command(BaseCommand):
    args = ''
    help = 'Upload images to EC2'

    def handle(self, *args, **options):
        rows = IntrinsicImagesDecomposition.objects.all() \
            .values_list('reflectance_image', 'shading_image')
        for names in progress_bar(rows):
            for n in names:
                upload_intrinsic_file.delay(n)
