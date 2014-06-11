import random
from django.core.management.base import BaseCommand

from celery import group

from common.utils import chunk_list_generator
from intrinsic.models import IntrinsicImagesDecomposition
from intrinsic.tasks import evaluate_decompositions_task


class Command(BaseCommand):
    args = ''
    help = '(Re)compute the error on all intrinsic image algorithms'

    def handle(self, *args, **options):
        thresh = 0.10

        qset = IntrinsicImagesDecomposition.objects.all() \
            .exclude(error_comparison_thresh=thresh) \
            .values_list('id', flat=True)

        delete_failed_open = False
        if len(args) >= 1 and args[0] == "delete-failed-open":
            delete_failed_open = True

        print 'delete_failed_open: %s' % delete_failed_open

        qset = list(qset)
        random.shuffle(qset)

        chunksize = max(len(qset) / 1024, 1)
        print 'Queuing tasks in chunks of %s items...' % chunksize
        job = group([
            evaluate_decompositions_task.subtask(kwargs={
                'decomposition_ids': ids,
                'delete_failed_open': delete_failed_open,
                'thresh': thresh,
            })
            for ids in chunk_list_generator(qset, chunksize)
        ])
        job.apply_async()

        print 'Done'
