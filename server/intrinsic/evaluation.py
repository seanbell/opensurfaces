import numpy as np
from scipy.misc import imread
from scipy.stats import rankdata
#from scipy.ndimage import interpolation

from imagekit.utils import open_image

from django.db.models import Count

from common.utils import progress_bar
from photos.models import Photo
from photos.utils import srgb_to_rgb
from intrinsic.models import IntrinsicPoint, IntrinsicPointComparison, \
    IntrinsicImagesDecomposition, IntrinsicImagesAlgorithm


def evaluate_error(photo_id, reflectance_image, thresh=0.10, is_sRGB=True):
    """
    Evaluate the error for intrinsic image decomposition of a photo.

    :param photo_id: photo being decomposed

    :param reflectance_image: candidate reflectance image (in sRGB space)

    :thresh when a user states ``A < B``, we interpret that to mean that ``A <
        B - thresh``.  This must be a positive value in order to ensure that
        a constant reflectance image receives a nonzero error.

    :return: dict corresponding to fields on an
        :class:`intrinsic.models.IntrinsicImagesDecomposition` object.
    """

    if isinstance(reflectance_image, basestring):
        reflectance_image = imread(reflectance_image).astype(float) / 255.0
    elif not isinstance(reflectance_image, np.ndarray):
        reflectance_image = np.asarray(reflectance_image).astype(float) / 255.0

    #if reflectance_image.shape[1] != 300:
        #z = 300.0 / reflectance_image.shape[1]
        #reflectance_image = interpolation.zoom(
            #reflectance_image, zoom=(z, z, 1))

    rows, cols, _ = reflectance_image.shape
    if is_sRGB:
        reflectance_image_linear = srgb_to_rgb(reflectance_image)
    else:
        reflectance_image_linear = reflectance_image

    # get the luminance of the reflectance channel

    # fetch comparisons
    comparisons = list(
        IntrinsicPointComparison.objects.filter(
            photo_id=photo_id,
            point1__opaque=True,
            point2__opaque=True,
            darker__isnull=False,
            darker__in=("1", "2", "E"),
            darker_score__isnull=False,
            darker_score__gt=0
        ).select_related('point1')
    )

    # fetch points
    points = IntrinsicPoint.objects.filter(photo_id=photo_id)
    point_id_to_l = {
        p.id: np.mean(reflectance_image_linear[int(p.y * rows), int(p.x * cols), :])
        for p in points
    }

    # ratio thresholds
    eq_thresh = 1.0 + thresh

    # error from a set of comparisons
    def comparison_error(comps):
        error_num = 0.0
        error_den = 0.0

        for c in comps:
            if c.darker not in ('1', '2', 'E'):
                raise ValueError("Unknown value of darker: %s" % c.darker)

            l1 = max(point_id_to_l[c.point1_id], 1e-10)
            l2 = max(point_id_to_l[c.point2_id], 1e-10)

            if l2 / l1 > eq_thresh:
                r_darker = '1'
            elif l1 / l2 > eq_thresh:
                r_darker = '2'
            else:
                r_darker = 'E'

            if c.darker != r_darker:
                error_num += c.darker_score
            error_den += c.darker_score

        if error_den:
            return error_num / error_den
        else:
            return None

    # return value
    update_kwargs = {
        'error_comparison_thresh': thresh,
    }

    # all errors
    update_kwargs['num'] = len(comparisons)
    if comparisons:
        update_kwargs['mean_error'] = comparison_error(comparisons)
    else:
        update_kwargs['mean_error'] = None

    # all dense errors
    comparisons_dense = [c for c in comparisons if c.point1.min_separation < 0.05]
    update_kwargs['num_dense'] = len(comparisons_dense)
    if comparisons_dense:
        update_kwargs['mean_dense_error'] = comparison_error(comparisons_dense)
    else:
        update_kwargs['mean_dense_error'] = None

    # all dense errors
    comparisons_sparse = [c for c in comparisons if c.point1.min_separation > 0.05]
    update_kwargs['num_sparse'] = len(comparisons_sparse)
    if comparisons_sparse:
        update_kwargs['mean_sparse_error'] = comparison_error(comparisons_sparse)
    else:
        update_kwargs['mean_sparse_error'] = None

    # equality errors
    comparisons_eq = [c for c in comparisons if c.darker == "E"]
    update_kwargs['num_eq'] = len(comparisons_eq)
    if comparisons_eq:
        update_kwargs['mean_eq_error'] = comparison_error(comparisons_eq)
    else:
        update_kwargs['mean_eq_error'] = None

    # inequality errors
    comparisons_neq = [c for c in comparisons if c.darker in ("1", "2")]
    update_kwargs['num_neq'] = len(comparisons_neq)
    if comparisons_neq:
        update_kwargs['mean_neq_error'] = comparison_error(comparisons_neq)
    else:
        update_kwargs['mean_neq_error'] = None

    # sum of two split errors
    if (update_kwargs['mean_eq_error'] is not None
            or update_kwargs['mean_neq_error'] is not None):
        f = lambda x: x if x else 0
        update_kwargs['mean_sum_error'] = (
            f(update_kwargs['mean_eq_error']) +
            f(update_kwargs['mean_neq_error']))
    else:
        update_kwargs['mean_sum_error'] = None

    return update_kwargs


def evaluate_decomposition(
        decomposition_id, delete_failed_open=False, **evaluate_kwargs):
    """
    Evaluate a decomposition and return the fields to be updated on
    the IntrinsicImagesDecomposition instance.

    :param delete_failed_open: if ``True``, delete decompositions that generate
        an error upon opening.  Warning: if there is an internet problem,
        enabling this will cause otherwise valid decompositions to be deleted.
    """

    from intrinsic.evaluation import evaluate_error

    # fetch reflectance image
    decomp = None
    try:
        decomp = IntrinsicImagesDecomposition.objects.get(id=decomposition_id)
        reflectance_image = open_image(decomp.reflectance_image)
    except KeyboardInterrupt:
        return
    except Exception as e:
        print e
        if delete_failed_open:
            print "Deleting: id %s (algorithm: %s %s)" % tuple(
                IntrinsicImagesDecomposition.objects
                .filter(id=decomposition_id).values_list('id', 'algorithm__slug', 'algorithm_id').get()
            )
            IntrinsicImagesDecomposition.objects.filter(id=decomposition_id).delete()

        return {
            k: None for k in IntrinsicImagesDecomposition.ERROR_ATTRS
        }

    # evaluate score
    update_kwargs = evaluate_error(decomp.photo_id, reflectance_image, **evaluate_kwargs)
    return update_kwargs


def completed_algorithm_ids(min_photos=10):
    all_algorithm_ids = IntrinsicImagesAlgorithm.objects \
        .filter(active=True).values_list('id', flat=True)

    return [
        a for a in all_algorithm_ids
        if (IntrinsicImagesDecomposition.objects
            .filter(photo__stylized=False,
                    photo__nonperspective=False,
                    photo__rotated=False,
                    mean_sum_error__isnull=False,
                    algorithm_id=a)
            .count() >= min_photos)
    ]


def completed_photo_ids(algorithm_ids):
    return Photo.objects \
        .filter(stylized=False, rotated=False, nonperspective=False) \
        .filter(intrinsic_images_decompositions__algorithm_id__in=algorithm_ids) \
        .filter(intrinsic_images_decompositions__mean_error__isnull=False) \
        .annotate(c=Count('intrinsic_images_decompositions')) \
        .filter(c__gt=len(algorithm_ids)) \
        .values_list('id', flat=True)


def algorithm_ranks(algorithm_ids, values, error_attr='mean_error',
                    show_progress=False):

    all_ranks = {id: [] for id in algorithm_ids}

    if show_progress:
        print 'organizing scores...'

    iterator = progress_bar(values) if show_progress else values
    photo_to_algs = {}
    for v in iterator:
        pid = v['photo_id']
        if pid in photo_to_algs:
            photo_to_algs[pid].append(v)
        else:
            photo_to_algs[pid] = [v]

    if show_progress:
        print 'ranking algorithms...'

    iterator = photo_to_algs.iteritems()
    if show_progress:
        iterator = progress_bar(iterator)
    for (photo_id, algs) in photo_to_algs.iteritems():
        if len(algs) < len(algorithm_ids):
            continue

        ranks = rankdata([v[error_attr] for v in algs], method='average')
        for i, v in enumerate(algs):
            all_ranks[v['algorithm_id']].append(ranks[i])

    return all_ranks


def algorithm_cv_errors(algorithm_slug, error_attr, show_progress=False):
    """
    Return the cross-validation errors for a single algorithm
    (``algorithm_slug``) according to error metric ``error_attr``.

    :param algorithm_slug: ``algorithm.slug``

    :param error_attr: attribute on
        :class:`intrinsic.models.IntrinsicImagesDecomposition`
        to fetch as the error

    :return: ``{ photo_id: error }``
    """

    # use the database-computed thresholds
    decomp_qset = IntrinsicImagesDecomposition.objects \
        .filter(algorithm__slug=algorithm_slug,
                algorithm__active=True,
                photo__stylized=False,
                photo__synthetic=False,
                photo__license__publishable=True) \
        .filter(**{error_attr + '__isnull': False})
    values = decomp_qset.values_list(
        'photo_id', 'algorithm_id', error_attr)

    photo_alg_to_error = {}
    for v in values:
        photo_alg_to_error[(v[0], v[1])] = v[2]

    photo_ids = _group_by_value(values, 0)
    algorithm_ids = _group_by_value(values, 1)

    algorithm_sums = {
        algorithm_id: np.sum([v[2] for v in algorithm_values])
        for algorithm_id, algorithm_values in algorithm_ids.iteritems()
    }

    cv_errors = {}
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


def algorithm_cv_ranking(algorithm_slugs=None, error_attr='mean_error',
                         show_progress=False):
    """
    Compute algorithm errors and rankings using cross-validation.

    :param algorithm_slugs: algorithms (by ``slug``) to consider.  If ``None``,
        then all algorithms with ``active=True`` are used.

    :param error_attr: error metric to use (attribute of
        ``IntrinsicImagesDecomposition``).

    :return: a ``dict`` with the following entries:

        .. code-block:: py

            {
                'slug_to_rank': { slug: (rank_mean, rank_std) }
                'slug_to_error': { slug: (error_mean, error_std) }
            }

        where ``slug`` is an entry from ``algorithm_slugs``, a
    """

    if not algorithm_slugs:
        algorithm_slugs = list(
            IntrinsicImagesAlgorithm.objects.filter(active=True)
            .order_by().distinct('slug').values_list('slug', flat=True)
        )

    if show_progress:
        print 'Evaluating %s algorithms: %s...' % (
            len(algorithm_slugs), algorithm_slugs)

    if show_progress:
        print 'Computing algorithm cross-validation errors...'

    # slug_to_photo_to_error: { slug: { photo: error } }
    slug_to_photo_to_error = {
        slug: algorithm_cv_errors(slug, error_attr)
        for slug in progress_bar(algorithm_slugs, show_progress)
    }

    # slug_to_errors: { slug: [error] }
    slug_to_errors = {
        slug: photo_to_error.values()
        for slug, photo_to_error in slug_to_photo_to_error.iteritems()
    }

    # slug_to_error: { slug: mean error, std error }
    slug_to_error = {
        slug: (np.mean(errors), np.std(errors))
        for slug, errors in slug_to_errors.iteritems()
    }

    if show_progress:
        print 'Computing ranks...'

    # photo_to_slug_error: { photo: [ (slug, error) ] }
    photo_to_slug_error = {}
    for slug, photo_ids in slug_to_photo_to_error.iteritems():
        for p, error in photo_ids.iteritems():
            if p in photo_to_slug_error:
                photo_to_slug_error[p].append((slug, error))
            else:
                photo_to_slug_error[p] = [(slug, error)]

    # slug_to_ranks: { slug: [ranks] }
    slug_to_ranks = {slug: [] for slug in algorithm_slugs}
    for photo, errors in photo_to_slug_error.iteritems():
        if len(errors) < len(algorithm_slugs):
            continue
        ranks = rankdata([e[1] for e in errors], method='average')
        for i, v in enumerate(errors):
            slug_to_ranks[v[0]].append(ranks[i])

    # slug_to_rank: { slug: mean rank, std rank }
    slug_to_rank = {
        slug: (np.mean(ranks), np.std(ranks))
        for slug, ranks in slug_to_ranks.iteritems()
    }

    if show_progress:
        print 'Computing ranks... done'

    return {
        'slug_to_rank': slug_to_rank,
        'slug_to_error': slug_to_error,
    }


def _group_by_value(values, idx):
    groups = {}
    for v in values:
        if v[idx] in groups:
            groups[v[idx]].append(v)
        else:
            groups[v[idx]] = [v]
    return groups
