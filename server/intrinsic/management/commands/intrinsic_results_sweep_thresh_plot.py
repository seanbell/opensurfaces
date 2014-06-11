import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

import pickle

from django.core.management.base import BaseCommand

from common.utils import progress_bar
from intrinsic.models import IntrinsicImagesDecomposition, IntrinsicImagesAlgorithm


class Command(BaseCommand):
    args = ''
    help = 'Plot error vs threshold for all algorithms and thresholds'

    def handle(self, *args, **options):
        basename = 'results_sweep_thresh'
        with open('%s.pkl' % basename) as f:
            thresh_to_attr_to_results = pickle.load(f)

        thresholds = sorted(thresh_to_attr_to_results.keys())

        algorithm_slugs = list(
            IntrinsicImagesAlgorithm.objects.filter(active=True)
            .order_by().distinct('slug').values_list('slug', flat=True)
        )

        for show_error in [True, False]:
            show_error_str = "yerr" if show_error else "nerr"
            for error_attr in progress_bar(IntrinsicImagesDecomposition.ERROR_ATTRS):
                for kind in ['rank', 'error']:
                    for i, slug in enumerate(algorithm_slugs):
                        val_std = [
                            thresh_to_attr_to_results[t][error_attr]['slug_to_%s' % kind][slug]
                            for t in thresholds
                        ]

                        vals = [x[0] for x in val_std]

                        if show_error:
                            stds = [x[1] for x in val_std]
                            thresholds_jitter = [t + i * 0.001 for t in thresholds]
                            plt.errorbar(thresholds_jitter, vals, yerr=stds)
                        else:
                            plt.plot(thresholds, vals)

                    plt.xlim([0.0, 1.0])
                    plt.ylim([0.0, (0.6 if kind == 'error' else 10.0)])
                    plt.legend(algorithm_slugs, prop={'size': 8})
                    plt.xlabel("delta")

                    plt.ylabel("%s%s" % (error_attr, " rank" if kind == "rank" else ""))

                    plt.savefig('%s-%s-%s.png' % (error_attr, kind, show_error_str))
                    plt.close()
