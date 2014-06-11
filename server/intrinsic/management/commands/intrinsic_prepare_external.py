import os
from django.core.management.base import BaseCommand

from common.utils import progress_bar
from intrinsic.tasks import export_photo_task


class Command(BaseCommand):
    args = ''
    help = 'Run all intrinsic image algorithms'

    def handle(self, *args, **options):
        image_size = 512
        photo_ids = [int(id) for id in open('photo-ids.txt').readlines()]

        outdir = 'photos-outdir/'
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        for photo_id in progress_bar(photo_ids):
            export_photo_task.delay(
                photo_id, image_size=image_size, outdir=outdir)
