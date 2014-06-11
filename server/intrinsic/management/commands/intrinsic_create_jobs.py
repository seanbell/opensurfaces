from django.core.management.base import BaseCommand

from common.utils import progress_bar

from photos.models import Photo
from django.db.models import F, Count, Avg
from intrinsic.algorithm import get_algorithm_variants
from intrinsic.models import IntrinsicImagesDecomposition, IntrinsicImagesAlgorithm
from intrinsic.tasks import intrinsic_decomposition_task, \
    intrinsic_decomposition_task_matlab


class Command(BaseCommand):
    args = ''
    help = 'Queue all intrinsic image algorithms'

    def handle(self, *args, **options):

        print 'Increment algorithm versions...'
        IntrinsicImagesAlgorithm.objects.all() \
            .update(task_version=F('task_version') + 1)

        print 'Fetching photos...'
        photo_ids = list(
            Photo.objects.filter(in_iiw_dataset=True)
            .order_by('id')
            .values_list('id', flat=True)
        )

        print 'Fetching algorithms...'
        algorithms = [
            IntrinsicImagesAlgorithm.objects.get_or_create(
                slug=a['slug'], parameters=a['parameters'],
                baseline=a['slug'].startswith('baseline_'))[0]
            for a in get_algorithm_variants()
        ]

        # HACK TO REMOVE
        algorithms += list(
            IntrinsicImagesAlgorithm.objects
            .filter(slug='bell2014_densecrf', active=True)
            .annotate(c=Count('intrinsic_images_decompositions'),
                      s=Avg('intrinsic_images_decompositions__mean_error'))
            .filter(c__gte=1000, s__lte=0.25)
        )

        print 'Filter out inactive or duplicate algorithms...'
        seen_algorithm_ids = set()
        distinct_algorithms = []
        for a in algorithms:
            if a.active and a.id not in seen_algorithm_ids:
                seen_algorithm_ids.add(a.id)
                distinct_algorithms.append(a)
        algorithms = distinct_algorithms

        for a in progress_bar(algorithms):
            if a.intrinsic_images_decompositions.exists():
                a._mean_error = a.intrinsic_images_decompositions \
                    .aggregate(s=Avg('mean_error'))['s']
            else:
                a._mean_error = 0.0
        algorithms.sort(key=lambda a: a._mean_error)

        c = [0, 0]
        print 'Starting jobs...'
        for algorithm in progress_bar(algorithms):
            completed_photo_ids = set(
                IntrinsicImagesDecomposition.objects
                .filter(algorithm_id=algorithm.id, mean_error__isnull=False, error_comparison_thresh=0.05)
                .values_list('photo_id', flat=True)
            )
            for photo_id in photo_ids:
                if photo_id in completed_photo_ids:
                    continue

                #if algorithm.slug.startswith('shen2011_') or algorithm.slug.startswith('zhao2012_'):
                if not algorithm.slug.startswith('bell2014_'):
                    intrinsic_decomposition_task_matlab.delay(
                        photo_id=photo_id,
                        algorithm_id=algorithm.id,
                        task_version=algorithm.task_version,
                    )
                    c[0] += 1
                else:
                    intrinsic_decomposition_task.delay(
                        photo_id=photo_id,
                        algorithm_id=algorithm.id,
                        task_version=algorithm.task_version,
                    )
                    c[1] += 1

        print "intrinsic_create_jobs: queued %s matlab, %s general tasks" % tuple(c)
