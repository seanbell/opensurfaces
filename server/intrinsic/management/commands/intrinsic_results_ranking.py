import os
import numpy as np
from django.core.management.base import BaseCommand
from django.db.models import Count

from scipy.stats import rankdata
from common.utils import progress_bar

from common.models import UserProfile
from photos.models import Photo
from mturk.models import ExperimentWorker
from intrinsic.models import IntrinsicPointComparisonResponse, \
    IntrinsicImagesAlgorithm, IntrinsicImagesDecomposition


SLUG_TO_TEX = {
    'baseline_reflectance': 'Baseline (const $R$)',
    'baseline_shading': 'Baseline (const $S$)',
    'garces2012_clustering': r'\cite{garces2012}',
    'shen2011_optimization': r'\cite{shen-CVPR2011b}',
    'bell2014_densecrf': r'\textbf{Our algorithm}',
    'bell2014_densecrf_prototype': r'\textbf{Our algorithm (prototype)}',
    'grosse2009_color_retinex': r'Retinex (color)',
    'grosse2009_grayscale_retinex': r'Retinex (gray)',
    'zhao2012_nonlocal': r'\cite{zhao-PAMI2012}',
}


class Command(BaseCommand):
    args = ''
    help = 'Evaluate all algorithms'

    def handle(self, *args, **options):
        #print 'Fetching user IDs...'
        #user_ids = self.get_user_ids()
        user_ids = []
        #print 'Using %s users' % len(user_ids)
        if not os.path.exists('generated'):
            os.makedirs('generated')

        self.photo_count = Photo.objects.filter(in_iiw_dataset=True).count()

        print 'Computing rankings...'
        for attr in ['mean_error', 'mean_dense_error', 'mean_sparse_error', 'mean_eq_error', 'mean_neq_error', 'mean_sum_error']:
            filename = 'generated/ranking_%s.tex' % attr
            with open(filename, 'w') as f:
                self.f = f
                self.evaluate_algorithms(user_ids, attr)
                self.f = None
            with open(filename) as f:
                print f.read()

        print 'Done'

    def evaluate_algorithms(self, user_ids, error_attr):
        algorithm_slugs = list(
            IntrinsicImagesAlgorithm.objects
            .filter(active=True)
            .exclude(slug__endswith='_prototype')
            .order_by().distinct('slug')
            .values_list('slug', flat=True)
        )

        # { slug: { photo_id : error } }
        print 'Evaluating algorithms...'
        slug_errors = {
            slug: self.algorithm_cv_errors(slug, error_attr)
            for slug in progress_bar(algorithm_slugs)
        }
        #algorithm_slugs.append('human')
        #slug_errors['human'] = self.human_errors(user_ids, error_attr)

        print 'Computing ranks (photo --> slug)...'

        # { photo: { slug: error } }
        photo_to_slugs = {}
        for slug, photo_ids in slug_errors.iteritems():
            for p, error in photo_ids.iteritems():
                if p in photo_to_slugs:
                    photo_to_slugs[p].append((slug, error))
                else:
                    photo_to_slugs[p] = [(slug, error)]

        print 'Computing ranks (slug --> ranks)...'

        # { slug: [ranks] }
        slug_ranks = {slug: [] for slug in algorithm_slugs}
        for photo, errors in photo_to_slugs.iteritems():
            if len(errors) < len(algorithm_slugs):
                continue
            ranks = rankdata([e[1] for e in errors], method='average')
            for i, v in enumerate(errors):
                slug_ranks[v[0]].append(ranks[i])

        print >>self.f, r"""
\begin{figure*}[tb]
\centering
\begin{subfigure}[b]{0.49\textwidth}
\begin{bchart}[max=65,plain,unit=\%,scale=0.8,width=1.2\textwidth]
""".strip()
        items = sorted(slug_ranks, key=lambda x: np.mean(slug_errors[x].values()))
        for slug in items:
            scale = (50 if error_attr == 'mean_sum_error' else 100)
            print >>self.f, r'  \bcbar[text={%s}]{%.1f}' % (
                SLUG_TO_TEX[slug],
                np.mean(slug_errors[slug].values()) * scale,
            )
        print >>self.f, r"""
\end{bchart}
\caption{%%
Weighted human disagreement (WHD), as described in
Section~\ref{ssec:metric}.
}
\end{subfigure}
\begin{subfigure}[b]{0.49\textwidth}
\begin{bchart}[min=0,max=8,plain,scale=0.8,width=1.2\textwidth]
""".strip()
        for slug in items:
            print >>self.f, r'  \bcbar[text={%s}]{%.2f}' % (
                SLUG_TO_TEX[slug],
                np.mean(slug_ranks[slug]),
            )
        print >>self.f, r"""
\end{bchart}
\caption{Mean rank (1 to 8).}
\end{subfigure}
\vspace{-6pt}
\caption{%
Quantitative comparison of our algorithm against several recent algorithms.
The ``median individual human'' is calculated using responses that were
excluded from the aggregation, and from users who were not blocked by our
sentinels.  We use NUM_USERS users for this test and NUM_TOTAL total users for
aggregation.}
}
\label{fig:ranking}
\end{figure*}
""".strip().replace('NUM_USERS', str(len(user_ids))) \
           .replace('NUM_TOTAL', str(IntrinsicPointComparisonResponse.objects.order_by().distinct('user').count()))
        self.f.flush()

    def algorithm_cv_errors(self, algorithm_slug, error_attr):
        """ cross-validation error """

        algorithm_ids = IntrinsicImagesAlgorithm.objects \
            .filter(slug=algorithm_slug, active=True) \
            .annotate(c=Count('intrinsic_images_decompositions')) \
            .filter(c__gte=self.photo_count)

        values = IntrinsicImagesDecomposition.objects \
            .filter(algorithm_id__in=algorithm_ids) \
            .filter(**{error_attr + '__isnull': False}) \
            .filter(photo__in_iiw_dataset=True) \
            .values_list('photo_id', 'algorithm_id', error_attr)

        photo_alg_to_error = {}
        for v in values:
            photo_alg_to_error[(v[0], v[1])] = v[2]

        cv_errors = {}

        photo_ids = group_by_value(values, 0)
        algorithm_ids = group_by_value(values, 1)

        algorithm_sums = {
            algorithm_id: np.sum([v[2] for v in algorithm_values])
            for algorithm_id, algorithm_values in algorithm_ids.iteritems()
        }

        for photo_id, photo_values in photo_ids.iteritems():
            algorithm_errors = []
            for algorithm_id, algorithm_values in algorithm_ids.iteritems():
                if (photo_id, algorithm_id) in photo_alg_to_error:
                    num = (algorithm_sums[algorithm_id] -
                           photo_alg_to_error[(photo_id, algorithm_id)])
                    e = float(num) / (len(algorithm_values) - 1)
                    algorithm_errors.append((algorithm_id, e))
            best_algorithm_id = min(algorithm_errors, key=lambda x: x[1])[0]
            cv_errors[photo_id] = photo_alg_to_error[(photo_id, best_algorithm_id)]

        assert len(cv_errors) > 0
        return cv_errors

    def get_user_ids(self):
        user_ids = IntrinsicPointComparisonResponse.objects.filter(user__exclude_from_aggregation=False) \
            .order_by().distinct('user').values_list('user_id', flat=True)
        return [
            u for u in progress_bar(user_ids) if (
                UserProfile.objects.filter(user_id=u, blocked=False).exists()
                and ExperimentWorker.objects.filter(
                    worker_id=u, blocked=False, num_test_correct__gte=20).exists()
            )
        ]

    def human_errors(self, user_ids, error_attr):
        print 'Fetching user responses...'
        all_user_values = IntrinsicPointComparisonResponse.objects \
            .filter(user__exclude_from_aggregation=False,
                    user_id__in=user_ids,
                    comparison__darker__isnull=False,
                    comparison__darker_score__gt=0,
                    comparison__photo__in_iiw_dataset=True) \
            .values_list('comparison__photo_id', 'darker',
                         'comparison__darker', 'comparison__darker_score',
                         'user_id', 'comparison__point1__min_separation')
        user_to_values = group_by_value(all_user_values, 4)

        photo_to_errors = {}
        user_mean_errors = []
        all_errors = []
        for user_id in progress_bar(user_ids):
            mean_errors = []
            photo_ids = group_by_value(user_to_values[user_id], 0)
            for photo_id, values in photo_ids.iteritems():
                if not values:
                    continue

                if error_attr == 'mean_error':
                    error_sum = np.sum(x[3] for x in values if x[1] != x[2])
                    error_total = np.sum(x[3] for x in values)
                    error = error_sum / error_total if error_total else None
                elif error_attr == 'mean_dense_error':
                    values1 = [x for x in values if x[5] < 0.05]
                    error_sum = np.sum(x[3] for x in values1 if x[1] != x[2])
                    error_total = np.sum(x[3] for x in values1)
                    error = error_sum / error_total if error_total else None
                elif error_attr == 'mean_sparse_error':
                    values1 = [x for x in values if x[5] > 0.05]
                    error_sum = np.sum(x[3] for x in values1 if x[1] != x[2])
                    error_total = np.sum(x[3] for x in values1)
                    error = error_sum / error_total if error_total else None
                elif error_attr == 'mean_eq_error':
                    values = [x for x in values if x[2] == 'E']
                    error_sum = np.sum(x[3] for x in values if x[1] != x[2])
                    error_total = np.sum(x[3] for x in values)
                    error = error_sum / error_total if error_total else None
                elif error_attr == 'mean_neq_error':
                    values = [x for x in values if x[2] in ('1', '2')]
                    error_sum = np.sum(x[3] for x in values if x[1] != x[2])
                    error_total = np.sum(x[3] for x in values)
                    error = error_sum / error_total if error_total else None
                elif error_attr == 'mean_sum_error':
                    values1 = [x for x in values if x[2] == 'E']
                    error_sum = np.sum(x[3] for x in values1 if x[1] != x[2])
                    error_total = np.sum(x[3] for x in values1)
                    error1 = error_sum / error_total if error_total else None

                    values2 = [x for x in values if x[2] in ('1', '2')]
                    error_sum = np.sum(x[3] for x in values2 if x[1] != x[2])
                    error_total = np.sum(x[3] for x in values2)
                    error2 = error_sum / error_total if error_total else None

                    if error1 is not None or error2 is not None:
                        error = (error1 if error1 else 0) + (error2 if error2 else 0)
                    else:
                        error = None
                else:
                    raise ValueError()

                if error is not None:
                    all_errors.append(error)
                    mean_errors.append(error)
                    if photo_id in photo_to_errors:
                        photo_to_errors[photo_id].append(error)
                    else:
                        photo_to_errors[photo_id] = [error]

            user_mean_errors.append(np.mean(mean_errors))

        #print >>self.f, 'ERROR METRIC: %s' % error_attr
        #print >>self.f, 'By User: User mean error: %s (%s) +/- %s, %s users' % (
            #np.mean(user_mean_errors),
            #np.median(user_mean_errors),
            #np.std(user_mean_errors),
            #len(user_mean_errors)
        #)
        #print >>self.f, 'Across all: User mean error: %s (%s) +/- %s, %s values' % (
            #np.mean(all_errors),
            #np.median(all_errors),
            #np.std(all_errors),
            #len(all_errors)
        #)
        #by_photo = [np.median(errors) for errors in photo_to_errors.values()]
        #print >>self.f, 'By photo: User mean error: %s (%s) +/- %s, %s values' % (
            #np.mean(by_photo),
            #np.median(by_photo),
            #np.std(by_photo),
            #len(by_photo)
        #)

        #for p in (5.0, 25.0, 50.0, 75.0, 95.0):
            #print >>self.f, 'Percentile %s: %s' % (np.percentile(user_mean_errors, p), p)
        self.f.flush()

        return {
            photo_id: np.median(errors)
            for photo_id, errors in photo_to_errors.iteritems()
        }


def group_by_value(values, idx):
    groups = {}
    for v in values:
        if v[idx] in groups:
            groups[v[idx]].append(v)
        else:
            groups[v[idx]] = [v]
    return groups
