import os
import pickle
import json
from celery import group

from django.core.management.base import BaseCommand
from common.utils import chunk_list_generator, \
    unit_interval_infinite_generator

from intrinsic.models import IntrinsicImagesDecomposition
from intrinsic.tasks import evaluate_decompositions_task
from intrinsic.evaluation import algorithm_cv_ranking


class Command(BaseCommand):
    args = ''
    help = 'Evaluate all algorithms, for a range of threshold values'

    def handle(self, *args, **options):
        basename = 'results_sweep_thresh'

        if os.path.exists('%s.pkl' % basename):
            with open('%s.pkl' % basename) as f:
                thresh_to_attr_to_results = pickle.load(f)
        else:
            thresh_to_attr_to_results = {}

        print 'Fetching decompositions...'
        self.decomp_ids = IntrinsicImagesDecomposition.objects.all() \
            .filter(photo__synthetic=False, algorithm__active=True) \
            .order_by('photo') \
            .values_list('id', flat=True)
        self.decomp_ids = list(self.decomp_ids)

        for thresh in unit_interval_infinite_generator():
            # avoid thresholds we've already computed
            if thresh < 1e-10 or any(abs(thresh - t) < 1e-10 for t in thresh_to_attr_to_results):
                continue

            # update error values
            self.compute_threshold(thresh=thresh)

            # recompute rankings
            attr_to_results = {}
            for attr in IntrinsicImagesDecomposition.ERROR_ATTRS:
                attr_to_results[attr] = algorithm_cv_ranking(
                    error_attr=attr, show_progress=True)

            thresh_to_attr_to_results[thresh] = attr_to_results

            print "Saving partial results to disk..."
            with open('%s.pkl' % basename, 'wb') as f:
                pickle.dump(thresh_to_attr_to_results, f)
            with open('%s.json' % basename, 'w') as f:
                json.dump(thresh_to_attr_to_results, f, sort_keys=True)

    def compute_threshold(self, thresh):
        # split task into 1024 chunks (too many subtasks causes a backlog
        # error)
        chunksize = len(self.decomp_ids) / 1024
        print 'Queuing %s items (chunksize %s) for threshold %s...' % (
            len(self.decomp_ids), chunksize, thresh)

        job = group([
            evaluate_decompositions_task.subtask(kwargs={
                'decomposition_ids': ids,
                'delete_failed_open': False,
                'thresh': thresh,
            })
            for ids in chunk_list_generator(self.decomp_ids, chunksize)
        ])
        result = job.apply_async()

        print 'Waiting on %s subtasks with chunksize %s...' % (
            len(self.decomp_ids) / chunksize, chunksize)

        result.join()
