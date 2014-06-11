import json
import timeit
import numpy as np

from django.db import transaction

from pilkit.processors import ResizeToFit
from photos.utils import rgb_to_srgb, srgb_to_rgb, \
    pil_to_numpy, numpy_to_pil
from common.utils import save_obj_attr_image
from photos.models import Photo
from intrinsic.models import IntrinsicImagesDecomposition, \
    IntrinsicImagesAlgorithm


def get_algorithm_variants():
    algs = []

    for gamma in (False, True):
        for td in (0.0003, 0.0005):
            for tv in (0.03, 0.05):
                for c in (0.001, 0.0015):
                    algs.append({
                        'slug': 'zhao2012_nonlocal',
                        'parameters': json.dumps({
                            'chrom_thresh': c,
                            'texture_patch_distance': td,
                            'texture_patch_variance': tv,
                            'gamma': gamma,
                        }, sort_keys=True)
                    })

    for gamma in (False, True):
        for td in (0.0005, 0.001, 0.002):
            for tv in (0.05, 0.1, 0.2):
                for c in (0.0003, 0.001, 0.0015):
                    algs.append({
                        'slug': 'zhao2012_nonlocal',
                        'parameters': json.dumps({
                            'chrom_thresh': c,
                            'texture_patch_distance': td,
                            'texture_patch_variance': tv,
                            'gamma': gamma,
                        }, sort_keys=True)
                    })

    for td in (0.0005, 0.0007, 0.001, 0.002):
        for tv in (0.03, 0.05, 0.1, 0.2):
            for c in (0.0015, 0.002, 0.005):
                algs.append({
                    'slug': 'zhao2012_nonlocal',
                    'parameters': json.dumps({
                        'chrom_thresh': c,
                        'texture_patch_distance': td,
                        'texture_patch_variance': tv,
                        'gamma': False,
                    }, sort_keys=True)
                })

    algs.append({
        'slug': 'baseline_reflectance',
        'parameters': json.dumps({}, sort_keys=True)
    })
    algs.append({
        'slug': 'baseline_shading',
        'parameters': json.dumps({}, sort_keys=True)
    })
    for w in (True, False):
        algs.append({
            'slug': 'shen2011_optimization',
            'parameters': json.dumps({
                'unmap_srgb': w,
                'wd': 3,
                'rho': 1.9,
            }, sort_keys=True),
        })
    algs.append({
        'slug': 'shen2011_optimization',
        'parameters': json.dumps({
            'unmap_srgb': True,
            'wd': 7,
            'rho': 1.9,
        }, sort_keys=True),
    })
    for w in (0.074989420933245579, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.70, 0.90):
        for w2 in (1.0, 0.37275937203149379, 0.3, 0.5):
            for L1 in (False, True):
                algs.append({
                    'slug': 'grosse2009_color_retinex',
                    'parameters': json.dumps({
                        'L1': L1,
                        'threshold_color': w,
                        'threshold_gray': w2,
                    }, sort_keys=True)
                })
    for w in (0.37275937203149379, 0.3, 0.5):
        for L1 in (False, True):
            algs.append({
                'slug': 'grosse2009_grayscale_retinex',
                'parameters': json.dumps({
                    'L1': L1,
                    'threshold': w,
                }, sort_keys=True)
            })
    for km_k in (3, 5, 6, 7, 8, 10, 12, 15, 30, 50, 100):
        for remap_gamma_2_2 in (False, True):
            algs.append({
                'slug': 'garces2012_clustering',
                'parameters': json.dumps({
                    'km_k': km_k,
                    'remap_gamma_2_2': remap_gamma_2_2,
                }, sort_keys=True)
            })

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

    from intrinsic.algorithm.bell2014.params import IntrinsicParameters

    # adjust each parameter by a bit
    bell2014_params = [default_params.copy()]
    for k, v in default_params.iteritems():
        if k == 'n_iters':
            for n in (1, 5, 15):
                p = default_params.copy()
                p[k] = n
                bell2014_params.append(p)
        elif k == 'abs_reflectance_weight':
            continue
        elif k in IntrinsicParameters.PARAM_CHOICES:
            choices = IntrinsicParameters.PARAM_CHOICES[k]
            for choice in choices:
                p = default_params.copy()
                p[k] = choice
                bell2014_params.append(p)
        elif isinstance(v, bool):
            p = default_params.copy()
            p[k] = not v
            bell2014_params.append(p)
        else:
            t = type(v)
            for multiplier in (0.1, 0.5, 2.0, 10.0):
                p = default_params.copy()
                p[k] = t(multiplier * v)
                bell2014_params.append(p)
            if k.endswith('_weight'):
                p = default_params.copy()
                p[k] = 0
                bell2014_params.append(p)
            if k == 'theta_c':
                p = default_params.copy()
                p[k] = 0.01
                bell2014_params.append(p)

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

    for k, v in best_params.iteritems():
        if k.endswith('_weight'):
            p = best_params.copy()
            p[k] = 0
            bell2014_params.append(p)
        elif isinstance(v, bool):
            p = best_params.copy()
            p[k] = not v
            bell2014_params.append(p)
        elif v == "L1":
            p = best_params.copy()
            p[k] = "L2"
            bell2014_params.append(p)
        elif v == "L2":
            p = best_params.copy()
            p[k] = "L1"
            bell2014_params.append(p)

    p = best_params.copy()
    p['shading_blur_method'] = 'bilateral'
    p['shading_blur_bilateral_sigma_range'] = 2.0
    bell2014_params.append(p)

    for shading_smooth_k in (2, 3, 4):
        p = best_params.copy()
        p['shading_smooth_k'] = shading_smooth_k
        bell2014_params.append(p)

    p = best_params.copy()
    p['n_iters'] = 1
    bell2014_params.append(p)

    p = best_params.copy()
    p['stage2_norm'] = 'L2'
    bell2014_params.append(p)

    p = best_params.copy()
    p['chromaticity_weight'] = 10
    bell2014_params.append(p)

    p = best_params.copy()
    p['abs_reflectance_weight'] = 10
    bell2014_params.append(p)

    p = best_params.copy()
    p['abs_reflectance_weight'] = 100
    bell2014_params.append(p)

    p = best_params.copy()
    p['abs_reflectance_weight'] = 1000
    bell2014_params.append(p)

    p = best_params.copy()
    p['abs_reflectance_weight'] = 10000
    bell2014_params.append(p)

    p = best_params.copy()
    p['n_iters'] = 2
    bell2014_params.append(p)

    p = best_params.copy()
    p['n_iters'] = 10
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_p'] = 0.001
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_p'] = 0.01
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_p'] = 0.01
    p['pairwise_weight'] = 1e5
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_l'] = 0.15
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_l'] = 0.2
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_l'] = 0.5
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_l'] = 0.05
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_p'] = 0.15
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_p'] = 0.2
    bell2014_params.append(p)

    p = best_params.copy()
    p['theta_p'] = 0.5
    bell2014_params.append(p)

    p = best_params.copy()
    p['shading_blur_init_method'] = 'image'
    bell2014_params.append(p)

    p = best_params.copy()
    p['shading_blur_init_method'] = 'constant'
    bell2014_params.append(p)

    p = best_params.copy()
    p['pairwise_weight'] = 1.1e4
    bell2014_params.append(p)

    p = best_params.copy()
    p['pairwise_weight'] = 0.9e4
    bell2014_params.append(p)

    p = best_params.copy()
    p['pairwise_weight'] = 1e3
    bell2014_params.append(p)

    p = best_params.copy()
    p['pairwise_weight'] = 1e2
    bell2014_params.append(p)

    p = best_params.copy()
    p['pairwise_weight'] = 1e1
    bell2014_params.append(p)

    for pairwise_weight in (0.75e4, 1.5e4):
        p = default_params.copy()
        p['n_iters'] = 25
        p['abs_shading_weight'] = 500.0
        p['chromaticity_weight'] = 0
        p['theta_c'] = 0.025
        p['shading_target_weight'] = 2e4
        p['shading_target_norm'] = 'L2'
        p['kmeans_n_clusters'] = 20
        p['pairwise_weight'] = pairwise_weight
        bell2014_params.append(p)

    for pairwise_intensity_chromaticity in (False, True):
        for b in (0, 1, 2):
            p = default_params.copy()
            if b == 0:
                p['shading_blur_iteration_pow'] = 2
                p['n_iters'] = 10
            elif b == 1:
                p['shading_blur_iteration_pow'] = 2
                p['n_iters'] = 20
            else:
                p['n_iters'] = 25
            if pairwise_intensity_chromaticity:
                p['pairwise_intensity_chromaticity'] = True
            p['abs_shading_weight'] = 500.0
            p['chromaticity_weight'] = 0
            p['theta_c'] = 0.025
            p['shading_target_weight'] = 2e4
            p['shading_target_norm'] = 'L2'
            p['kmeans_n_clusters'] = 20
            bell2014_params.append(p)

    # manual sets of parameters to try
    for shading_smooth_k in (2, 3, 4, 5):
        p = default_params.copy()
        p['shading_smooth_k'] = shading_smooth_k
        p['abs_shading_weight'] = 1e2
        p['pairwise_intensity_chromaticity'] = True
        p['n_iters'] = 30
        p['chromaticity_weight'] = 0
        p['theta_c'] = 0.025
        p['shading_target_weight'] = 2e4
        p['shading_target_norm'] = 'L2'
        p['kmeans_n_clusters'] = 20
        bell2014_params.append(p)

    for kmeans_n_clusters in (10, 15, 20):
        p = default_params.copy()
        p['shading_smooth_k'] = 5
        p['abs_shading_weight'] = 1e2
        p['pairwise_intensity_chromaticity'] = True
        p['n_iters'] = 30
        p['chromaticity_weight'] = 0
        p['theta_c'] = 0.025
        p['shading_target_weight'] = 2e4
        p['shading_target_norm'] = 'L2'
        p['kmeans_n_clusters'] = 20
        bell2014_params.append(p)

    for kmeans_n_clusters in (20, 30):
        for stage2_chromaticity in (False, True):
            p = default_params.copy()
            p['pairwise_intensity_chromaticity'] = True
            p['n_iters'] = 30
            p['chromaticity_weight'] = 0
            p['theta_c'] = 0.025
            p['shading_target_weight'] = 2e4
            p['shading_target_norm'] = 'L2'
            p['kmeans_n_clusters'] = kmeans_n_clusters
            if stage2_chromaticity:
                p['stage2_chromaticity'] = True
            bell2014_params.append(p)

    for abs_shading_weight in (1e1, 1e2, 3e2):
        for shading_blur_sigma in (0.1, 0.2):
            p = default_params.copy()
            p['abs_shading_weight'] = abs_shading_weight
            p['shading_blur_sigma'] = shading_blur_sigma
            p['shading_target_weight'] = 2e4
            p['theta_c'] = 0.025
            p['kmeans_n_clusters'] = 20
            p['n_iters'] = 25
            p['pairwise_intensity_chromaticity'] = True
            p['chromaticity_weight'] = 0
            p['shading_target_norm'] = 'L2'
            bell2014_params.append(p)

    for shading_target_weight in (2e4, 2.5e4):
        for kmeans_n_clusters in (15, 20, 30, 40):
            p = default_params.copy()
            p['shading_target_weight'] = shading_target_weight
            p['kmeans_n_clusters'] = kmeans_n_clusters
            p['abs_shading_weight'] = 1e2
            p['theta_c'] = 0.025
            p['n_iters'] = 25
            p['pairwise_intensity_chromaticity'] = True
            p['chromaticity_weight'] = 0
            p['shading_target_norm'] = 'L2'
            bell2014_params.append(p)

    for n_iters in (20, 30):
        for shading_target_weight in (1e4, 2e4):
            for kmeans_n_clusters in (20, 40, 50):
                p = default_params.copy()
                p['n_iters'] = n_iters
                p['shading_target_weight'] = shading_target_weight
                p['kmeans_n_clusters'] = kmeans_n_clusters
                p['pairwise_intensity_chromaticity'] = True
                p['theta_c'] = 0.025
                p['chromaticity_weight'] = 0
                p['shading_target_norm'] = 'L2'
                bell2014_params.append(p)

    for shading_target_weight in (1e4, 2e4, 3e4):
        for theta_c in (0.01, 0.015):
            p = default_params.copy()
            p['n_iters'] = 20
            p['shading_target_weight'] = shading_target_weight
            p['kmeans_n_clusters'] = kmeans_n_clusters
            p['pairwise_intensity_chromaticity'] = True
            p['theta_c'] = theta_c
            p['chromaticity_weight'] = 0
            p['shading_target_norm'] = 'L2'
            bell2014_params.append(p)

    for abs_shading_weight in (0.5e3, 1.5e3):
        for shading_target_weight in (2e4, 2.5e4):
            for theta_c in (0.02, 0.025):
                for kmeans_n_clusters in (20, 30):
                    p = default_params.copy()
                    p['abs_shading_weight'] = abs_shading_weight
                    p['shading_target_weight'] = shading_target_weight
                    p['kmeans_n_clusters'] = kmeans_n_clusters
                    p['theta_c'] = theta_c
                    p['n_iters'] = 25
                    p['pairwise_intensity_chromaticity'] = True
                    p['chromaticity_weight'] = 0
                    p['shading_target_norm'] = 'L2'
                    bell2014_params.append(p)

    for pairwise_weight in (0.5e4, 1e4, 2e4):
        for shading_target_weight in (2e4, 2.5e4):
            for theta_c in (0.02, 0.025):
                for kmeans_n_clusters in (20, 30):
                    p = default_params.copy()
                    p['shading_target_weight'] = shading_target_weight
                    p['pairwise_weight'] = pairwise_weight
                    p['theta_c'] = theta_c
                    p['kmeans_n_clusters'] = kmeans_n_clusters
                    p['n_iters'] = 30
                    p['pairwise_intensity_chromaticity'] = True
                    p['chromaticity_weight'] = 0
                    p['shading_target_norm'] = 'L2'
                    bell2014_params.append(p)

    for theta_c in (0.01, 0.025):
        for chromaticity_weight in (0, 10, 100):
            p = default_params.copy()
            p['pairwise_intensity_chromaticity'] = True
            p['n_iters'] = 20
            p['shading_target_weight'] = 1e4
            p['theta_c'] = theta_c
            p['chromaticity_weight'] = chromaticity_weight
            p['shading_target_norm'] = 'L2'
            p['shading_target_chromaticity'] = True
            bell2014_params.append(p)

    for theta_c in (0.01, 0.025):
        for chromaticity_weight in (0, 10, 100):
            p = default_params.copy()
            p['theta_c'] = theta_c
            p['chromaticity_weight'] = chromaticity_weight
            p['pairwise_intensity_chromaticity'] = True
            bell2014_params.append(p)

    for theta_c in (0.01, 0.025):
        for chromaticity_weight in (0, 10):
            for shading_blur_init_method in ('image', 'none'):
                for L2 in (False, True):
                    p = default_params.copy()
                    p['theta_c'] = theta_c
                    p['chromaticity_weight'] = chromaticity_weight
                    p['shading_blur_init_method'] = shading_blur_init_method
                    p['n_iters'] = 20
                    p['shading_target_weight'] = 1e4
                    p['pairwise_intensity_chromaticity'] = True
                    if L2:
                        p['shading_target_norm'] = 'L2'
                    bell2014_params.append(p)

    for theta_c in (0.01, 0.025):
        for shading_target_weight in (1.5e4, 1e5):
            p = default_params.copy()
            p['theta_c'] = theta_c
            p['shading_target_weight'] = shading_target_weight
            p['pairwise_intensity_chromaticity'] = True
            p['shading_target_norm'] = 'L2'
            p['n_iters'] = 20
            bell2014_params.append(p)

    for theta_p in (0.1, 0.2):
        for stage2_L2 in (False, True):
            for shading_target_weight in (1e4, 1.5e4):
                p = default_params.copy()
                p['theta_p'] = theta_p
                p['shading_target_weight'] = shading_target_weight
                p['theta_c'] = 0.025
                p['pairwise_intensity_chromaticity'] = True
                p['shading_target_norm'] = 'L2'
                p['chromaticity_norm'] = 'L2'
                if stage2_L2:
                    p['stage2_norm'] = 'L2'
                p['n_iters'] = 20
                bell2014_params.append(p)

    p = default_params.copy()
    p['abs_reflectance_weight'] = 1
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_reflectance_weight'] = 10
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_reflectance_weight'] = 100
    bell2014_params.append(p)

    for r in (1, 10, 100, 1000):
        for s in (1, 10, 100):
            p = default_params.copy()
            p['abs_reflectance_weight'] = r
            p['abs_shading_weight'] = s
            bell2014_params.append(p)

    p = default_params.copy()
    p['abs_reflectance_weight'] = 100
    p['abs_shading_weight'] = 0
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_reflectance_weight'] = 1000
    p['abs_shading_weight'] = 0
    bell2014_params.append(p)

    for k in (2, 3, 4):
        p = default_params.copy()
        p['shading_smooth_k'] = k
        bell2014_params.append(p)

    p = default_params.copy()
    p['theta_c'] = 0.05
    bell2014_params.append(p)

    p = default_params.copy()
    p['theta_c'] = 0.025
    p['shading_smooth_k'] = 2
    p['chromaticity_weight'] = 100
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_shading_weight'] = 10
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_shading_weight'] = 10
    p['abs_shading_gray_point'] = 1.0
    bell2014_params.append(p)

    p = default_params.copy()
    p['chromaticity_weight'] = 1000
    p['split_clusters'] = False
    bell2014_params.append(p)

    p = default_params.copy()
    p['chromaticity_weight'] = 1000
    p['split_clusters'] = False
    p['shading_blur_init_method'] = 'image'
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_shading_weight'] = 10
    p['split_clusters'] = False
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_shading_weight'] = 10
    p['chromaticity_weight'] = 100
    p['split_clusters'] = False
    bell2014_params.append(p)

    p = default_params.copy()
    p['kmeans_n_clusters'] = 5
    bell2014_params.append(p)

    p = default_params.copy()
    p['kmeans_n_clusters'] = 10
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_shading_weight'] = 10
    p['chromaticity_weight'] = 1000
    p['split_clusters'] = False
    bell2014_params.append(p)

    p = default_params.copy()
    p['abs_shading_weight'] = 10
    p['abs_reflectance_weight'] = 10
    p['chromaticity_weight'] = 1000
    p['split_clusters'] = False
    bell2014_params.append(p)

    p = default_params.copy()
    p['n_iters'] = 20
    bell2014_params.append(p)

    p = default_params.copy()
    p['n_iters'] = 20
    p['abs_shading_weight'] = 100
    p['chromaticity_weight'] = 1000
    p['theta_c'] = 0.025
    p['shading_blur_init_method'] = 'image'
    bell2014_params.append(p)

    p = default_params.copy()
    p['chromaticity_weight'] = 1000
    p['theta_c'] = 0.025
    p['pairwise_weight'] = 1500
    bell2014_params.append(p)

    p = default_params.copy()
    p['theta_c'] = 0.01
    p['abs_shading_weight'] = 100
    bell2014_params.append(p)

    for a in (1000, 2000, 5000):
        for b in (0.02, 0.025):
            for c in ('image', 'none'):
                p = default_params.copy()
                p['chromaticity_weight'] = a
                p['theta_c'] = b
                p['shading_blur_init_method'] = c
                bell2014_params.append(p)

    for a in (0, 100, 1000):
        for b in (100, 1000, 10000):
            for c in (0, 10):
                for d in ('image', 'none'):
                    p = default_params.copy()
                    p['theta_c'] = 0.025
                    p['abs_shading_weight'] = a
                    p['chromaticity_weight'] = b
                    p['abs_reflectance_weight'] = c
                    p['shading_blur_init_method'] = d
                    bell2014_params.append(p)

    p = default_params.copy()
    p['theta_c'] = 0.01
    p['chromaticity_weight'] = 0
    bell2014_params.append(p)

    p = default_params.copy()
    p['theta_c'] = 0.01
    p['chromaticity_weight'] = 0
    p['abs_shading_weight'] = 100
    bell2014_params.append(p)

    for p in bell2014_params:
        algs.append({
            'slug': 'bell2014_densecrf',
            'parameters': json.dumps(p, sort_keys=True),
        })

    return algs


def baseline_reflectance(photo, **kwargs):
    """ Return chromaticity as reflectance (constant intensity) and pixel
    intensity as shading """
    def function(image, **kwargs):
        image = srgb_to_rgb(pil_to_numpy(image))
        s = np.clip(np.sum(image, axis=-1), 1e-3, float('inf'))
        r = image / s[:, :, np.newaxis]
        return r, s
    return _run_algorithm(photo, function, 'baseline_reflectance', baseline=True)


def baseline_shading(photo, **kwargs):
    """ Return the image as reflectance and constant for shading """
    def function(image, **kwargs):
        image = srgb_to_rgb(pil_to_numpy(image))
        return image, np.ones_like(image)
    return _run_algorithm(photo, function, 'baseline_shading', baseline=True)


def grosse2009_color_retinex(photo, L1=True,
                             threshold_color=0.074989420933245579,
                             threshold_gray=1.0):
    parameters = {
        'threshold_color': threshold_color,
        'threshold_gray': threshold_gray,
        'L1': L1,
    }

    def function(image, **kwargs):
        from intrinsic.algorithm.grosse2009 import intrinsic
        image = srgb_to_rgb(pil_to_numpy(image)) * 255.0
        mask = np.ones((image.shape[0:2]), dtype=bool)
        s, r = intrinsic.color_retinex(image, mask, **kwargs)
        r = image / np.clip(s, 1e-3, float('inf'))[:, :, np.newaxis]
        return r, s

    return _run_algorithm(photo, function, 'grosse2009_color_retinex', parameters)


def grosse2009_grayscale_retinex(photo, threshold=0.37275937203149379, L1=True):
    parameters = {
        'threshold': threshold,
        'L1': L1,
    }

    def function(image, **kwargs):
        from intrinsic.algorithm.grosse2009 import intrinsic
        image = srgb_to_rgb(pil_to_numpy(image)) * 255.0
        image_gray = np.mean(image, axis=2)
        mask = np.ones((image_gray.shape[0:2]), dtype=bool)
        s, r = intrinsic.retinex(image_gray, mask, **kwargs)
        r = image / np.clip(s, 1e-3, float('inf'))[:, :, np.newaxis]
        return r, s

    return _run_algorithm(photo, function, 'grosse2009_grayscale_retinex', parameters)


def shen2011_optimization(photo, **parameters):
    def function(image, **kwargs):
        from intrinsic.algorithm import shen2011
        return shen2011.run(image, **kwargs)

    return _run_algorithm(photo, function, 'shen2011_optimization', parameters)


def garces2012_clustering(photo, **parameters):

    def function(image, **kwargs):
        from intrinsic.algorithm import garces2012
        return garces2012.run(image, **kwargs)

    return _run_algorithm(photo, function, 'garces2012_clustering', parameters)


def zhao2012_nonlocal(photo, **parameters):

    def function(image, **kwargs):
        from intrinsic.algorithm import zhao2012
        return zhao2012.run(image, **kwargs)

    return _run_algorithm(photo, function, 'zhao2012_nonlocal', parameters)


def gehler2011_sparsity(photo):
    parameters = {
        'downsample': 1
    }

    def function(image, **kwargs):
        from intrinsic.algorithm import gehler2011
        return gehler2011.run(image, **kwargs)

    return _run_algorithm(photo, function, 'gehler2011_sparsity', parameters)


def bell2014_densecrf(photo, **parameters):

    def function(image, **kwargs):
        from intrinsic.algorithm.bell2014.solver import IntrinsicSolver
        from intrinsic.algorithm.bell2014.input import IntrinsicInput
        solver = IntrinsicSolver(
            input=IntrinsicInput(
                image_rgb=srgb_to_rgb(pil_to_numpy(image)),
            ),
            params=parameters,
        )
        r, s, decomposition = solver.solve()
        return r, s

    return _run_algorithm(photo, function, 'bell2014_densecrf', parameters)


def _run_algorithm(photo, function, slug, parameters={},
                   image_size=512, baseline=False):
    """ Sets up an algorithm in the database, calls ``function``, then stores
    the result in the database """

    if not isinstance(photo, Photo):
        time_start = timeit.default_timer()
        r, s = function(image=photo, **parameters)
        time_end = timeit.default_timer()
        runtime = time_end - time_start
        r, s = [process_layer(x) for x in (r, s)]
        return r, s, runtime

    # ensure a consistent order for parameters
    algorithm, _ = IntrinsicImagesAlgorithm.objects.get_or_create(
        slug=slug, parameters=json.dumps(parameters, sort_keys=True), baseline=baseline)

    if IntrinsicImagesDecomposition.objects.filter(
            photo=photo, algorithm=algorithm).exists():
        print '_run_algorithm: EXISTS: photo %s, algorithm %s, params %s' % (
            photo.id, slug, parameters)
        return
    else:
        print '_run_algorithm: starting: photo %s, algorithm %s, params %s' % (
            photo.id, slug, parameters)

    # load and resize image (do it here rather than load the pre-resized photo
    # thumbnail to avoid jpg artifacts)
    attr = '_intrinsic_algorithm_photo_%s' % image_size
    if hasattr(photo, attr):
        image = getattr(photo, attr)
    else:
        image = photo.open_image(width='orig')
        image = ResizeToFit(image_size, image_size).process(image)
        setattr(photo, attr, image)

    time_start = timeit.default_timer()
    # r, s: linar numpy arrays
    r, s = function(image=image, **parameters)
    time_end = timeit.default_timer()
    runtime = time_end - time_start

    # r, s: sRGB numpy arrays
    r, s = [process_layer(x) for x in (r, s)]

    # r, s: sRGB PIL images
    reflectance_image = numpy_to_pil(r)
    shading_image = numpy_to_pil(s)

    # save in database
    with transaction.atomic():
        decomposition, _ = IntrinsicImagesDecomposition.objects \
            .get_or_create(photo=photo, algorithm=algorithm)

        # fill in fields
        decomposition.runtime = runtime
        save_obj_attr_image(
            decomposition, attr='reflectance_image',
            img=reflectance_image, format='png', save=False)
        save_obj_attr_image(
            decomposition, attr='shading_image',
            img=shading_image, format='png', save=False)

        # comupte error
        from intrinsic.evaluation import evaluate_error
        update_kwargs = evaluate_error(photo.id, reflectance_image)
        for k, v in update_kwargs.iteritems():
            setattr(decomposition, k, v)

        # save to database
        decomposition.save()

    print '_run_algorithm: DONE: photo %s, algorithm %s, params %s, runtime: %s' % (
        photo.id, slug, parameters, runtime)

    return r, s, runtime


# rescale and convert to sRGB
def process_layer(r):
    if not isinstance(r, np.ndarray):
        r = np.asarray(r).astype(float) / 255.0
    if r.ndim < 3:
        r2 = np.empty((r.shape[0], r.shape[1], 3), dtype=float)
        r2[:, :, :] = r[:, :, np.newaxis]
        r = r2
    r /= np.percentile(r, 99.9)
    return rgb_to_srgb(r)
