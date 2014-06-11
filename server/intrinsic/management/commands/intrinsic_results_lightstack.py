import numpy as np
from pilkit.utils import open_image
from decimal import Decimal
from django.core.management.base import BaseCommand

from common.utils import progress_bar
from photos.utils import srgb_to_rgb
from photos.models import PhotoLightStack
from intrinsic.models import IntrinsicImagesAlgorithm, \
    IntrinsicImagesDecomposition


DARKER_TO_IDX = {
    "E": 0,
    "1": 1,
    "2": 2,
}


class Command(BaseCommand):
    args = ''
    help = 'Analyze light stacks'

    def handle(self, *args, **options):
        self.user_change()
        #self.alg_change()

    def alg_change(self):
        algorithms = IntrinsicImagesAlgorithm.objects.filter(active=True) \
            .order_by('slug', '-id')
        algorithm_errors = {
            alg: [] for alg in algorithms
        }

        light_stacks = PhotoLightStack.objects.all()

        for alg in progress_bar(algorithms):
            use_alg = True
            for light_stack in light_stacks:
                photo_ids = light_stack.photos.values_list('id', flat=True)

                decompositions = IntrinsicImagesDecomposition.objects.filter(
                    algorithm=alg, photo_id__in=photo_ids)

                if len(decompositions) != len(photo_ids):
                    use_alg = False
                    break

                errors = []
                for d1 in decompositions:
                    r1 = open_image(d1.reflectance_image)
                    r1 = srgb_to_rgb(np.asarray(r1).astype(float) / 255.0)
                    r1 = np.mean(r1, axis=-1)

                    for d2 in decompositions:
                        if d1.photo_id == d2.photo_id:
                            continue
                        r2 = open_image(d2.reflectance_image)
                        r2 = srgb_to_rgb(np.asarray(r2).astype(float) / 255.0)
                        r2 = np.mean(r2, axis=-1)

                        errors.append(lmse(r1, r2))
                algorithm_errors[alg].append(np.mean(errors))

            if use_alg:
                print alg.slug, alg.id, \
                    np.mean(algorithm_errors[alg]), \
                    np.median(algorithm_errors[alg]), \
                    np.std(algorithm_errors[alg])

        errors = [
            (alg, np.mean(errors), np.median(errors), np.std(errors))
            for alg, errors in algorithm_errors.iteritems()
            if len(errors) == len(light_stacks)
        ]
        errors.sort(key=lambda x: x[1])

        for alg, e, m, s in errors:
            print alg.slug, alg.id, e, m, s

    def user_change(self):

        for min_separation in [Decimal('0.03'), Decimal('0.07')]:
            sum_confusion_matrix = np.zeros((3, 3))
            eq_weight = 0.0
            neq_weight = 0.0
            eq_count = 0.0
            neq_count = 0.0
            for light_stack in PhotoLightStack.objects.all():
                confusion_matrix = np.zeros((3, 3))
                confusion_matrix_count = np.zeros((3, 3))

                photos = light_stack.photos.all()
                print '%s photos' % len(photos)
                for photo1 in photos:
                    comparisons1 = photo1.intrinsic_comparisons \
                        .filter(darker__isnull=False,
                                point1__min_separation=min_separation) \
                        .select_related('point1', 'point2')
                    map1 = comparisons_to_map(comparisons1)
                    for photo2 in photos:
                        if photo1.id == photo2.id:
                            continue

                        comparisons2 = photo2.intrinsic_comparisons \
                            .filter(darker__isnull=False,
                                    point1__min_separation=min_separation) \
                            .select_related('point1', 'point2')

                        for c2 in progress_bar(comparisons2):
                            c1 = map1.get(comparison_key(c2), None)

                            if c1:
                                confusion_matrix[
                                    DARKER_TO_IDX[c1.darker],
                                    DARKER_TO_IDX[c2.darker]
                                ] += 0.5 * (c1.darker_score + c2.darker_score)

                                if c1.darker == c2.darker:
                                    eq_weight += c1.darker_score
                                    eq_weight += c2.darker_score
                                    eq_count += 2.0
                                else:
                                    neq_weight += c1.darker_score
                                    neq_weight += c2.darker_score
                                    neq_count += 2.0

                sum_confusion_matrix += confusion_matrix
                #print 'photo', min_separation, confusion_matrix // 2

            #print min_separation, sum_confusion_matrix // 2

            print min_separation, 'equal', eq_weight / eq_count
            print min_separation, 'ineq', neq_weight / neq_count

            print min_separation, 1 - (
                float(np.trace(sum_confusion_matrix)) /
                np.sum(sum_confusion_matrix)
            )


def comparison_key(c):
    return (round(c.point1.min_separation * 100),
            round(c.point1.x * 1000),
            round(c.point1.y * 1000),
            round(c.point2.x * 1000),
            round(c.point2.y * 1000))


def comparisons_to_map(comparisons):
    return {
        comparison_key(c): c
        for c in comparisons
    }


############################# Error metric #####################################

def lmse(r1, r2):
    assert r1.shape == r2.shape
    return local_error(r1, r2, np.ones_like(r1), 20, 10)


def ssq_error(correct, estimate, mask):
    """Compute the sum-squared-error for an image, where the estimate is
    multiplied by a scalar which minimizes the error. Sums over all pixels
    where mask is True. If the inputs are color, each color channel can be
    rescaled independently."""
    assert correct.ndim == 2
    if np.sum(estimate**2 * mask) > 1e-5:
        alpha = np.sum(correct * estimate * mask) / np.sum(estimate**2 * mask)
    else:
        alpha = 0.
    return np.sum(mask * (correct - alpha*estimate) ** 2)


def local_error(correct, estimate, mask, window_size, window_shift):
    """Returns the sum of the local sum-squared-errors, where the estimate may
    be rescaled within each local region to minimize the error. The windows are
    window_size x window_size, and they are spaced by window_shift."""
    M, N = correct.shape[:2]
    ssq = total = 0.
    for i in range(0, M - window_size + 1, window_shift):
        for j in range(0, N - window_size + 1, window_shift):
            correct_curr = correct[i:i+window_size, j:j+window_size]
            estimate_curr = estimate[i:i+window_size, j:j+window_size]
            mask_curr = mask[i:i+window_size, j:j+window_size]
            ssq += ssq_error(correct_curr, estimate_curr, mask_curr)
            total += np.sum(mask_curr * correct_curr**2)
    assert -np.isnan(ssq/total)

    return ssq / total
