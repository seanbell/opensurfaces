from django.core.management.base import BaseCommand

import os
from celery import group


from intrinsic.models import IntrinsicPointComparison
from intrinsic.tasks import export_dataset_photo_task


class Command(BaseCommand):
    args = ''
    help = 'Export the IIW (Intrinsic Images in the Wild) dataset'

    def handle(self, *args, **options):
        out_dir = args[0] if len(args) > 0 else 'intrinsic-dataset-export'
        out_dir = os.path.abspath(out_dir)

        comparisons_qset = IntrinsicPointComparison.objects.filter(
            darker__isnull=False,
            photo__in_iiw_dataset=True,
        )

        print 'Scheduling jobs...'
        all_photo_ids = comparisons_qset \
            .order_by().distinct('photo') \
            .values_list('photo_id', flat=True)

        photo_ids = []
        for photo_id in all_photo_ids:
            image_filename = '%s.png' % photo_id
            json_filename = '%s.json' % photo_id
            if (not os.path.exists(os.path.join(out_dir, image_filename)) or
                    not os.path.exists(os.path.join(out_dir, json_filename))):
                photo_ids.append(photo_id)

        job = group(
            export_dataset_photo_task.s(photo_id, out_dir)
            for photo_id in photo_ids
        )
        job.apply_async()

        print 'Done: scheduled %s jobs (%s photos already exported)' % (
            len(photo_ids), len(all_photo_ids) - len(photo_ids))
