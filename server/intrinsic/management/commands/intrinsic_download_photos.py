import os
import shutil
from django.core.management.base import BaseCommand

from common.utils import progress_bar

from photos.models import Photo
from intrinsic.models import IntrinsicPointComparison


class Command(BaseCommand):
    args = ''
    help = 'Download all photos referenced by a comparison object'

    def handle(self, *args, **options):

        if len(args) < 1:
            print 'Usage: ./manage.py intrinsic_download_photos <outdir>'
            return

        outdir = args[0]
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        photo_ids = IntrinsicPointComparison.objects \
            .filter(darker_score__gt=0, darker__isnull=False) \
            .order_by() \
            .distinct('photo') \
            .values_list('photo_id')

        qset = Photo.objects.filter(id__in=photo_ids)
        for p in progress_bar(qset):
            image = p.image_512
            filename = os.path.join(outdir, '%s.jpg' % p.id)
            with open(filename, 'wb') as f:
                image.seek(0)
                shutil.copyfileobj(image, f)
