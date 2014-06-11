from decimal import Decimal
from django.conf import settings
from django.db.models import F, Q

from photos.models import Photo
from intrinsic.models import IntrinsicPoint, IntrinsicPointOpacityResponse, \
    IntrinsicPointComparison, IntrinsicPointComparisonResponse


def configure_experiments():
    """ This function is automatically called by
    the command ./manage.py mtconfigure """

    from mturk.utils import configure_experiment
    production = not settings.MTURK_SANDBOX

    configure_experiment(
        slug='intrinsic_opacity',
        template_dir='intrinsic/experiments',
        module='intrinsic.experiments',
        version=2,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.05'),
        num_outputs_max=5,
        contents_per_hit=200,   # if production else 50,
        frame_height=668,  # handle 1024x768 window sizes
        content_type_model=IntrinsicPoint,
        out_content_type_model=IntrinsicPointOpacityResponse,
        out_content_attr='point',
        content_filter={
            #'photo__license__publishable': True,
            #'photo__stylized': False,
            #'photo__rotated': False,
            #'photo__nonperspective': False,
            #'photo__synthetic': True,
            'photo__intrinsic_synthetic__multilayer_exr__isnull': False,
            #'photo__scene_category_correct': True,
            #'photo__num_intrinsic_points__gte': 20,
            #'min_separation__lt': 0.05,
        },
        title='Click on mirrors and transparent surfaces',
        description='Given points in images, your job is to decide which belong to mirrors or transparent objects.',
        keywords='category,images,collection,image,picture,classify,color',
        requirements={},
        auto_add_hits=True,
        has_tutorial=True,
    )

    # don't add photo 10386; it's somewhat ambiguous
    # don't add photo 94610 -- it's all gloss and metal
    excluded_photo_ids = [10386, 94610]

    # hard-code examples here for now
    equal_tests = IntrinsicPointComparison.objects.in_bulk(list(set([
        961869, 961802, 961774, 961815, 961848, 961789, 961814, 961888, 961868,
        961885, 961713, 961742, 961818, 961813, 961864, 961807, 961743, 961766,
        961784, 961884, 961714, 999517, 999510, 1006818, 1006825, 1006838,
        1006808, 1006820, 1006810, 1046422, 1046444, 1046369, 1046437, 1046352,
        1046338, 1046425, 1046459, 929022, 929035, 929037, 929031, 929008,
        928985, 929006, 929035, 2385973, 2386026, 2385959, 2386106, 2385974,
        1605947, 1605914, 1605960, 1605989, 1605962, 1606032, 1605956, 1605931,
        1605946, 1605988, 1606043, 1606044, 1118334, 1118351, 1118282, 1118347,
        1118422, 1118329, 1118260, 1118410, 1118350, 1118443, 1118311, 1118306,
        1118404, 1118362, 1118286, 1118405, 1118345, 1118287, 1118335, 1118367,
        1118395, 1118390, 1118308, 1118400, 1118434, 1118301, 1118425, 1118439,
        1118369, 1118415, 1118281, 1118288, 1118362, 2419322, 2419219, 2419210,
        2419204, 956745, 956741, 956641, 928997, 928997, 928981, 1720063,
        1720071, 1719956, 1719978, 1720041, 1720042, 1719928, 1720011, 1719905,
        1719973, 1720059, 1719918, 1720012, 1720080, 1719915, 1720025, 1719974,
        1719943, 1719908, 1719922, 1720044, 1720013, 1402497, 1402598, 1402545,
        1719916, 1719958, 1720078, 1720628, 1720590, 1720606, 1720641, 1320564,
        1320545, 1320547, 1320548, 2432036, 3708799, 3445549, 1118283, 1118258,
        2508708, 951758, 951741, 951662, 951758, 951717, 951620, 951712, 951629,
    ]))).values()
    for comparison in equal_tests:
        if comparison.photo_id not in excluded_photo_ids:
            comparison.darker = 'E'
            comparison.darker_method = 'A'
            comparison.save()

    point1_tests = IntrinsicPointComparison.objects.in_bulk([
        961811, 961865, 961759, 999516, 999490, 999491, 999583, 999500, 999564,
        1046371, 2358770, 2358731, 1118331, 1118290, 1118263, 1118302, 2358729,
        2358731, 2358695, 1180756, 1180681, 1180720, 1180701, 1180673, 976878,
        976878, 999565, 1720053, 1719988, 1719951, 1402559, 1720077, 1720629,
        1320551, 1320549, 1320627, 1320606, 1320622, 2431927, 2432017, 2431952,
        2432053, 2431947, 2432055, 3708827, 3708860, 3708802, 3708808, 3708899,
        3708874, 3708845, 3445595, 3445598, 3445566, 3445584, 3445498, 3708895,
        3708908, 3708894, 3889277, 3889277, 3889172, 961827, 961769, 961891,
        961725, 961744, 2369862, 2369839, 2369873, 2508687, 2508663, 2508695,
        2508631
    ]).values()
    for comparison in point1_tests:
        if comparison.photo_id not in excluded_photo_ids:
            comparison.darker = '1'
            comparison.darker_method = 'A'
            comparison.save()

    point2_tests = IntrinsicPointComparison.objects.in_bulk([
        999515, 999498, 999499, 999569, 999562, 1046453, 2358755, 2358801,
        2358691, 1118365, 1118418, 2358714, 2358755, 956602, 956601, 1180669,
        1180730, 976827, 976825, 1719954, 1720019, 1402521, 1402562, 1720565,
        1320579, 2431925, 2431989, 2431923, 2432011, 3708773, 3708878, 3445472,
        3445554, 3445586, 3445550, 3445609, 3445556, 3445546, 3889199, 3889278,
        3889145, 2208252, 2369764, 2508705, 2508711
    ]).values()
    for comparison in point2_tests:
        if comparison.photo_id not in excluded_photo_ids:
            comparison.darker = '2'
            comparison.darker_method = 'A'
            comparison.save()

    test_contents = [t for t in (equal_tests + point1_tests + point2_tests)
                     if t.photo_id not in excluded_photo_ids]

    configure_experiment(
        slug='intrinsic_compare',
        template_dir='intrinsic/experiments',
        module='intrinsic.experiments',
        version=2,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.06'),
        num_outputs_max=5,
        contents_per_hit=25,  # if production else 2,
        max_active_hits=10000 if production else 50,
        frame_height=668,  # handle 1024x768 window sizes
        content_type_model=IntrinsicPointComparison,
        out_content_type_model=IntrinsicPointComparisonResponse,
        out_content_attr='comparison',
        content_filter={
            'point1__opaque': True,
            'point2__opaque': True,
            'photo__intrinsic_synthetic__multilayer_exr__isnull': False,
            #'photo__license__publishable': True,
            #'photo__stylized': False,
            #'photo__rotated': False,
            #'photo__nonperspective': False,
            #'photo__synthetic': False,
            #'photo__scene_category_correct': True,
            #'point1__min_separation__lt': 0.05,
        },
        title='Compare colors in an image',
        description='Given pairs of points in images, your job is to decide which of two points is darker.',
        keywords='category,images,collection,image,picture,classify,color',
        requirements={},
        auto_add_hits=True,
        has_tutorial=True,
        test_contents=test_contents,
        test_contents_per_assignment=5,
    )


def update_votes_cubam(show_progress=False):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task """

    from mturk.models import Experiment
    from mturk.cubam import update_votes_cubam

    # responses that we will consider
    opacity_responses = IntrinsicPointOpacityResponse.objects \
        .filter(invalid=False) \
        .exclude(point__opaque_method='A') \
        .order_by()

    update_votes_cubam(
        object_model=IntrinsicPoint,
        labels=opacity_responses,
        object_attr='point_id',
        label_attr='opaque',
        object_label_attr='opaque',
        quality_method_attr='opaque_method',
        score_threshold=0,
        min_votes=4,
        show_progress=show_progress,
        return_changed_objects=False,
        experiment_filter={'slug': 'intrinsic_opacity'}
    )

    # Since we have a 3-way answer, we break it down into two questions:
    # 1) are the two points the same reflectance?
    # 2) if not, does the darker pixel have darker reflectance?
    #
    # With this breakdown, we hope to capture use biases.  A relatively common
    # failure case of the experiment is that users always click the
    # darker pixel.  Another common case is that they always indicate "E"
    # (same).  These biases should be well captured by this breakdown.

    # we have to manually mark it as dirty inbetween our two stages since
    # our dirty tracking system assumes only one run of CUBAM
    cubam_dirty = any(Experiment.objects
                      .filter(slug='intrinsic_compare')
                      .values_list('cubam_dirty', flat=True))

    # responses that we will consider
    darker_responses = IntrinsicPointComparisonResponse.objects \
        .filter(invalid=False, user__exclude_from_aggregation=False) \
        .order_by()

    # CUBAM for question 1
    update_votes_cubam(
        object_model=IntrinsicPointComparison,
        labels=darker_responses,
        object_attr='comparison_id',
        label_attr='reflectance_eq',
        object_label_attr='reflectance_eq',
        quality_method_attr='darker_method',
        score_threshold=0,
        min_votes=4,
        show_progress=show_progress,
        return_changed_objects=False,
        experiment_filter={'slug': 'intrinsic_compare'}
    )

    # items that are updated
    comparisons = IntrinsicPointComparison.objects \
        .exclude(darker_method='A') \
        .order_by()

    # convert back to our 3-way representation (1, 2, E)
    comparisons.filter(reflectance_eq=True).update(
        darker="E", reflectance_dd=None, reflectance_dd_score=None,
        darker_score=F('reflectance_eq_score')
    )

    # the dirty-tracking doesn't handle two-stage updates like this one,
    # so we manually mark it as dirty
    if cubam_dirty:
        Experiment.objects \
            .filter(slug='intrinsic_compare') \
            .update(cubam_dirty=True)

    # CUBAM for question 2, only considering the entries that branched as False
    # from question 1
    dd_responses = darker_responses.filter(
        reflectance_eq=False, reflectance_dd__isnull=False)

    update_votes_cubam(
        object_model=IntrinsicPointComparison,
        labels=dd_responses,
        object_attr='comparison_id',
        label_attr='reflectance_dd',
        object_label_attr='reflectance_dd',
        quality_method_attr='darker_method',
        score_threshold=0,
        min_votes=1,
        show_progress=show_progress,
        return_changed_objects=False,
        experiment_filter={'slug': 'intrinsic_compare'}
    )

    if cubam_dirty:

        if show_progress:
            print 'Updating changed IntrinsicPointComparison instances...'

        # convert back to our 3-way representation (1, 2, E)
        comparisons.filter(reflectance_eq=False) \
            .filter(Q(point1_image_darker=True, reflectance_dd=True) |
                    Q(point1_image_darker=False, reflectance_dd=False)) \
            .update(darker="1")
        comparisons.filter(reflectance_eq=False) \
            .filter(Q(point1_image_darker=True, reflectance_dd=False) |
                    Q(point1_image_darker=False, reflectance_dd=True)) \
            .update(darker="2")

        comparisons.filter(reflectance_eq=False, reflectance_dd=True) \
            .update(darker_score=F('reflectance_dd_score'))
        comparisons.filter(reflectance_eq=False, reflectance_dd=False) \
            .update(darker_score=0 - F('reflectance_dd_score'))

        if show_progress:
            print 'Updating all Photo instances...'

        # update photos (faster to just list all the ids than to try and figure out
        # what changed since there are so many objects)
        from photos.tasks import update_photos_num_intrinsic
        photo_ids = Photo.objects.all().order_by().values_list('id', flat=True)
        update_photos_num_intrinsic(list(photo_ids), show_progress=show_progress)

    return None


def update_changed_objects(changed_objects):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task
    with all objects that were changed by new votes.  """

    pass


def make_reject_message(experiment, hit, perc):
    """ Return a reject message for when the submission performs too poorly
    with sentinel objects.  Return ``None`` to use a default message.  This
    function is called by ``mturk.views.external.make_reject_message``.  """

    if experiment.slug == "intrinsic_compare":
        if perc <= 5:
            return (
                "We took a random sample of your answers but none of them "
                "matched against our correct answers.  Usually this happens when "
                "you aren't correctly ignoring lighting.  For example, if two "
                "points are on wall, but one is highlighted by a lamp, they "
                "should have the same surface color."
            )
        elif perc <= 20:
            return (
                "We took a random sample of your answers but almost none of them "
                "matched against our correct answers.  Usually this happens when "
                "you aren't correctly ignoring lighting.  For example, if two "
                "points are on wall, but one is highlighted by a lamp, they "
                "should have the same surface color."
            )
        elif perc <= 50:
            return (
                "We took a random sample of your answers but less than half of them "
                "matched our correct answers.  Usually this happens when "
                "you aren't correctly ignoring lighting.  For example, if two "
                "points are on wall, but one is highlighted by a lamp, they "
                "should have the same surface color."
            )
    else:
        # default message
        return None


def content_priority(experiment, obj):
    """ Return a priority to assign to ``obj`` for an experiment.  Higher
    priority objects are shown first. """

    score = 0
    if hasattr(obj, 'photo'):
        photo = obj.photo
        score += photo.publishable_score()
        if photo.synthetic and photo.intrinsic_synthetic is not None:
            score += 10000000
        if photo.light_stack:
            score += 1000000
        if not photo.num_intrinsic_points:
            score += photo.num_intrinsic_points
    return score
