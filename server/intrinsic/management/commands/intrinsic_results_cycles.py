import numpy as np
from django.core.management.base import BaseCommand

from scipy.stats import rankdata
from common.utils import progress_bar

from common.models import UserProfile
from mturk.models import ExperimentWorker
from intrinsic.models import IntrinsicPointComparisonResponse, \
    IntrinsicImagesAlgorithm, IntrinsicImagesDecomposition


class Command(BaseCommand):
    args = ''
    help = 'Evaluate all algorithms'

    def handle(self, *args, **options):
        filename = 'cycles.tex'

        photo_ids = list(
            Photo.objects.filter(num_intrinsic_comparisons__gt=0)
            .values_list('id', flat=True)
        )

        for pid in photo_id:
            points = list(IntrinsicPoint.objects.filter(photo_id=pid).select_related('intrinsic_comparisons'))
            for p in points:
                for comparison in p.intrinsic_comparisons:
