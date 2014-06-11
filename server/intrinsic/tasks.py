import os
import json
from celery import shared_task

from django.conf import settings
from django.db import transaction
from django.db.models import Count, F, Avg

from imagekit.utils import open_image
from pilkit.processors import ResizeToFit

from photos.utils import numpy_to_pil
from common.utils import save_obj_attr_image, progress_bar

from intrinsic.sampling import sample_photo_intrinsic_points, \
    sample_photo_intrinsic_comparisons

from intrinsic.models import IntrinsicPoint, IntrinsicImagesDecomposition, \
    IntrinsicImagesAlgorithm
from photos.models import Photo


@shared_task
def sample_intrinsic_points_task(
        photo_id, min_edges=1, **kwargs):
    """ Sample points and edges for a photo """

    if (IntrinsicPoint.objects.filter(
            photo_id=photo_id, min_separation=kwargs['min_separation']).exists()):
        print "Samples already exist for photo %s" % photo_id
        return

    # if this fails, we don't want a partially sampled image
    with transaction.atomic():
        existing_point_ids = IntrinsicPoint.objects \
            .filter(photo_id=photo_id) \
            .values_list('id', flat=True)

        photo = Photo.objects.get(id=photo_id)
        sample_photo_intrinsic_points(photo, **kwargs)
        sample_photo_intrinsic_comparisons(photo, **kwargs)

        # delete points with too few edges
        while True:
            # want n1 + n2 > min_edges ==> n1 > min_edges - n2
            qset = IntrinsicPoint.objects \
                .filter(photo_id=photo_id, min_separation=kwargs['min_separation']) \
                .annotate(n1=Count('comparison_point1'),
                          n2=Count('comparison_point2')) \
                .filter(n1__lt=min_edges - F('n2')) \
                .exclude(id__in=existing_point_ids)  # don't delete existing points

            if qset.exists():
                qset.delete()
            else:
                break


@shared_task()
def intrinsic_update_training_result(show_progress=False):
    """ Update the error on IntrinsicImagesAlgorithm objects """

    IntrinsicImagesAlgorithm.objects.all().update(
        iiw_best=False, iiw_mean_error=None)

    slugs = IntrinsicImagesAlgorithm.objects.all() \
        .order_by('slug') \
        .distinct('slug') \
        .values_list('slug', flat=True)

    photos = Photo.objects.filter(in_iiw_dataset=True)
    num_photos = photos.count()
    if show_progress:
        photo_ids = list(photos.values_list('id', flat=True))

    for slug in slugs:
        if show_progress:
            print slug

        algorithms = IntrinsicImagesAlgorithm.objects \
            .filter(active=True, slug=slug) \
            .order_by('id')
        if show_progress:
            algorithms = progress_bar(algorithms)

        best_algorithm = None
        for algorithm in algorithms:
            iiw_decompositions = IntrinsicImagesDecomposition.objects.filter(
                algorithm=algorithm,
                photo__in_iiw_dataset=True,
                mean_error__isnull=False)

            num_decompositions = iiw_decompositions.count()
            if num_decompositions < num_photos:
                if show_progress:
                    decomp_photo_ids = set(iiw_decompositions.values_list('photo_id', flat=True))
                    if num_photos - num_decompositions < 10:
                        missing_ids = []
                        for p in photo_ids:
                            if p not in decomp_photo_ids:
                                missing_ids.append(p)
                        print "Algorithm %s (id: %s): missing %s photos %s" % (
                            slug, algorithm.id, num_photos - num_decompositions, missing_ids)
                    else:
                        print "Algorithm %s (id: %s): missing %s photos" % (
                            slug, algorithm.id, num_photos - num_decompositions)
                continue

            iiw_mean_error = iiw_decompositions.aggregate(a=Avg('mean_error'))['a']
            iiw_mean_runtime = iiw_decompositions.aggregate(a=Avg('runtime'))['a']

            algorithm.iiw_mean_error = iiw_mean_error
            algorithm.iiw_mean_runtime = iiw_mean_runtime
            algorithm.save()

            if not best_algorithm or iiw_mean_error < best_algorithm.iiw_mean_error:
                best_algorithm = algorithm

        if best_algorithm:
            best_algorithm.iiw_best = True
            best_algorithm.save()


@shared_task(queue='matlab')
def intrinsic_decomposition_task_matlab(*args, **kwargs):
    """ Decomposition task that requires MATLAB.  This just calls
    ``intrinsic_decomposition_task``, but is a separate function for routing to
    the ``matlab`` celery queue. """

    intrinsic_decomposition_task(*args, **kwargs)


@shared_task(queue='intrinsic')
def intrinsic_decomposition_task(photo_id, algorithm_id, task_version=0):
    """
    Decompose an image with a given algorithm and set of parameters.  The image
    is resized to fit in a 512 by 512 box.  The resize operation happens in the
    file's storage colorspace (likely sRGB).

    :param photo_id: ``photo.id``

    :param algorithm_id: ``algorithm.id``
    """

    #algorithm, _ = IntrinsicImagesAlgorithm.objects.get_or_create(
        #slug=algorithm_slug, parameters=json.dumps(parameters, sort_keys=True),
        #baseline=algorithm_slug.startswith('baseline_'))

    algorithm = IntrinsicImagesAlgorithm.objects.get(id=algorithm_id)
    parameters = json.loads(algorithm.parameters)

    if task_version != algorithm.task_version:
        print "Version changed (%s --> %s): exiting" % (
            task_version, algorithm.task_version)
        return
    elif not algorithm.active:
        print "Algorithm not active: %s %s: exiting" % (
            algorithm.slug, algorithm.parameters)
        return
    elif IntrinsicImagesDecomposition.objects.filter(
            photo_id=photo_id, algorithm=algorithm).exists():
        print "Already decomposed: photo_id: %s, algorithm: %s %s: exiting" % (
            photo_id, algorithm.slug, algorithm.parameters)
        return

    print 'intrinsic_decomposition_task: photo_id: %s, slug: %s, parameters: %s' % (
        photo_id, algorithm.slug, parameters
    )

    # download image
    photo = Photo.objects.get(id=photo_id)
    image = ResizeToFit(512, 512).process(photo.open_image(width='orig'))

    # decompose
    import intrinsic.algorithm
    func = getattr(intrinsic.algorithm, algorithm.slug)
    r, s, runtime = func(image, **parameters)
    r = numpy_to_pil(r)
    s = numpy_to_pil(s)

    # save: use atomic so that if the image save fails, the record is not kept
    with transaction.atomic():
        decomposition, _ = IntrinsicImagesDecomposition.objects \
            .get_or_create(photo_id=photo_id, algorithm=algorithm)

        decomposition.runtime = runtime
        save_obj_attr_image(
            decomposition, attr='reflectance_image',
            img=r, format='png', save=False)
        save_obj_attr_image(
            decomposition, attr='shading_image',
            img=s, format='png', save=False)

        from intrinsic.evaluation import evaluate_error
        update_kwargs = evaluate_error(photo_id, r)
        for k, v in update_kwargs.iteritems():
            setattr(decomposition, k, v)

        decomposition.save()


@shared_task
def evaluate_decompositions_task(
        decomposition_ids, delete_failed_open=False,
        **evaluate_kwargs):

    """ Evaluate the error on a list of decomposition ``id``s. """

    from intrinsic.evaluation import evaluate_decomposition
    for decomposition_id in decomposition_ids:
        update_kwargs = evaluate_decomposition(
            decomposition_id,
            delete_failed_open=delete_failed_open,
            **evaluate_kwargs)

        IntrinsicImagesDecomposition.objects \
            .filter(id=decomposition_id) \
            .update(**update_kwargs)


from django.core.files.storage import FileSystemStorage
INTRINSIC_STORAGE = FileSystemStorage(
    location=settings.MEDIA_ROOT,
    base_url=settings.MEDIA_URL,
)


@shared_task
def upload_intrinsic_file(name):
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    default_storage.save(
        name, ContentFile(INTRINSIC_STORAGE.open(name).read())
    )
    INTRINSIC_STORAGE.delete(name)


@shared_task
def export_dataset_photo_task(photo_id, out_dir):
    photo = Photo.objects.filter(id=photo_id).select_related(
        'license',
        'intrinsic_points',
        'intrinsic_points__opacities',
        'intrinsic_comparisons'
        'intrinsic_comparisons__responses',
    )[0]

    image_filename = '%s.png' % photo_id
    json_filename = '%s.json' % photo_id

    intrinsic_points = photo.intrinsic_points.all()
    intrinsic_comparisons = photo.intrinsic_comparisons.all()

    intrinsic_points = intrinsic_points.filter(
        opaque__isnull=False,
    )
    intrinsic_comparisons = intrinsic_comparisons.filter(
        point1__opaque=True,
        point2__opaque=True,
        darker__isnull=False,
        darker__in=("1", "2", "E"),
        darker_score__isnull=False,
        darker_score__gt=0
    )

    intrinsic_points = [
        {
            'id': p.id,
            'x': p.x,
            'y': p.y,
            'sRGB': p.sRGB,
            'min_separation': float(p.min_separation),
            'opaque': p.opaque,
            'opaque_score': p.opaque_score,
            'opaque_method': p.opaque_method,
            'opaque_responses': [
                {
                    'id': r.id,
                    'mturk_worker_id': r.user.mturk_worker_id,
                    'opaque': r.opaque,
                    'time_ms': r.time_ms,
                    'time_active_ms': r.time_active_ms,
                }
                for r in p.opacities.filter(invalid=False).order_by('id')
            ]
        } for p in intrinsic_points
    ]

    intrinsic_comparisons = [
        {
            'id': c.id,
            'point1': c.point1_id,
            'point2': c.point2_id,
            'min_separation': float(min(c.point1.min_separation, c.point2.min_separation)),
            'darker': c.darker,
            'darker_score': c.darker_score,
            'darker_method': c.darker_method,
            'darker_responses': [
                {
                    'id': r.id,
                    'mturk_worker_id': r.user.mturk_worker_id,
                    'darker': r.darker,
                    'confidence': r.confidence,
                    'time_ms': r.time_ms,
                    'time_active_ms': r.time_active_ms,
                }
                for r in c.responses.filter(invalid=False).order_by('id')
            ]
        } for c in intrinsic_comparisons
    ]

    if photo.flickr_user_id:
        attribution_name = photo.flickr_user.display_name
        attribution_url = photo.get_flickr_url()
    else:
        attribution_name = photo.attribution_name
        attribution_url = photo.attribution_url

    data = {
        'photo': photo_id,
        'image_filename': image_filename,
        'aspect_ratio': photo.aspect_ratio,
        'flickr_user': photo.flickr_user.username if photo.flickr_user_id else None,
        'flickr_id': photo.flickr_id,
        'license': {
            'name': photo.license.name,
            'url': photo.license.url,
            'cc': photo.license.creative_commons,
        },
        'light_stack': photo.light_stack_id,
        'attribution_name': attribution_name,
        'attribution_url': attribution_url,
        'intrinsic_points': intrinsic_points,
        'intrinsic_comparisons': intrinsic_comparisons,
    }

    if not os.path.exists(out_dir):
        try:
            os.makedirs(out_dir)
        except:
            # this could be multiple attempts to create the same directory.
            # the file-write step will fail if this is a true fail.
            pass

    with open(os.path.join(out_dir, json_filename), 'w') as f:
        f.write(json.dumps(data, indent=2, sort_keys=True))

    image = ResizeToFit(512, 512).process(open_image(photo.image_orig))
    image.save(os.path.join(out_dir, image_filename))
