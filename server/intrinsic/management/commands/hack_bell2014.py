import json
from django.core.management.base import BaseCommand

from common.utils import progress_bar

from django.db.models import Avg, StdDev
from photos.models import Photo
from intrinsic.models import IntrinsicImagesDecomposition, \
    IntrinsicImagesAlgorithm


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):

        algs = IntrinsicImagesAlgorithm.objects.filter(
            slug='bell2014_densecrf',
            active=True,
        )

        result = []

        for a in progress_bar(algs):
            params = json.loads(a.parameters)

            if ('pairwise_weight' not in params or
                    params['n_iters'] > 60 or params['n_iters'] < 1):

                print "Disabling", a.id, ' '
                a.active = False
                a.save()
                continue

            decomps = IntrinsicImagesDecomposition.objects \
                .filter(algorithm=a,
                        error_comparison_thresh=0.10,
                        photo__in_iiw_dataset=True) \

            count = decomps.count()

            if count > 150:
                whd = decomps.aggregate(s=Avg('mean_error'))['s']
                runtime = a.intrinsic_images_decompositions.aggregate(s=Avg('runtime'))['s']
                result.append((whd, runtime, count, a))
            else:
                print a.id, count, ' '

        default_params = {
            'n_iters': 10,
            'shading_blur_sigma': 0.1,
            'shading_blur_init_method': 'none',
            'kmeans_intensity_scale': 0.5,
            'kmeans_n_clusters': 30,
            'abs_reflectance_weight': 0,
            'abs_shading_weight': 1e3,
            'abs_shading_gray_point': 0.5,
            'shading_target_weight': 1e3,
            'chromaticity_weight': 10,
            'pairwise_weight': 1e4,
            'theta_p': 0.1,
            'theta_l': 0.1,
            'theta_c': 0.03,
            'split_clusters': True,
        }

        p = default_params.copy()
        p['n_iters'] = 25
        p['abs_shading_weight'] = 500.0
        p['chromaticity_weight'] = 0
        p['theta_c'] = 0.025
        p['shading_target_weight'] = 2e4
        p['pairwise_intensity_chromaticity'] = True
        p['shading_target_norm'] = 'L2'
        p['kmeans_n_clusters'] = 20
        best_params = p

        result.sort(key=lambda x: x[0], reverse=True)
        for whd, runtime, count, a in result:
            params = json.loads(a.parameters)

            diff = {}
            for k, v in params.iteritems():
                if k in default_params:
                    if v != default_params[k]:
                        diff[k] = '%s --> %s' % (default_params[k], v)
                else:
                    diff[k] = '[default] --> %s' % v

            print 'id: %s, count: %s, whd: %.1f%%, runtime: %s s, params: %s' % (
                a.id, count, whd * 100.0, runtime, diff)

        print '-' * 30
        print '\n' * 2

        algorithm_ids = []

        for whd, runtime, count, a in result:
            params = json.loads(a.parameters)

            c = 0
            for k, v in params.iteritems():
                if v != best_params.get(k):
                    c += 1
            if c > 2:
                continue

            diff = {}
            for k, v in params.iteritems():
                if k in best_params:
                    if v != best_params[k]:
                        diff[k] = '%s --> %s' % (best_params[k], v)
                else:
                    diff[k] = '[default] --> %s' % v

            print 'id: %s, count: %s, whd: %.1f%%, runtime: %s s, params: %s' % (
                a.id, count, whd * 100.0, runtime, diff)

            algorithm_ids.append(a.id)

        ## find photo where changing parameters has biggest effect
        #photo_ids = list(
            #Photo.objects.filter(in_iiw_dataset=True)
            #.filter(num_intrinsic_comparisons__gt=40)
            #.order_by('id')
            #.values_list('id', flat=True)
        #)

        #vals = []
        #for photo_id in progress_bar(photo_ids):
            #std = IntrinsicImagesDecomposition.objects \
                #.filter(photo_id=photo_id, algorithm_id__in=algorithm_ids) \
                #.aggregate(s=StdDev('mean_error'))['s']
            #vals.append((photo_id, std))
        #vals.sort(key=lambda x: x[1], reverse=True)
        #for v in vals[:100]:
            #print v
