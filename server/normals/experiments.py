from decimal import Decimal

from shapes.models import Shape, MaterialShape
from normals.models import ShapeRectifiedNormalLabel, ShapeRectifiedNormalQuality


def configure_experiments():
    """ This function is automatically called by
    the command ./manage.py mtconfigure """

    # must be imported locally to avoid a circular import
    from mturk.utils import configure_experiment

    configure_experiment(
        slug='rectify_continuous',
        template_dir='normals/experiments',
        module='normals.experiments',
        examples_group_attr='shape',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.10'),
        num_outputs_max=1,
        contents_per_hit=10,
        content_type_model=MaterialShape,
        out_content_type_model=ShapeRectifiedNormalLabel,
        out_content_attr='shape',
        content_filter={
            'invalid': False,
            'planar': True,
            'pixel_area__gt': 10 * Shape.MIN_PLANAR_AREA,
            'num_vertices__gte': 4,
            'correct': True,
            'substance__isnull': False,
            'substance__fail': False,
            #'photo__whitebalanced': True,
            'photo__scene_category_correct': True,
            'photo__nonperspective': False,
        },
        title='Rotate an image in 3D',
        description='Rotate a thumbtack so that a 3D image looks like it is facing the camera.',
        keywords='flat,planar,appearance,polygon,shape,draw,image,picture,3D,graphics',
        requirements={},
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
    )

    configure_experiment(
        slug='quality_rectify',
        template_dir='normals/experiments',
        module='normals.experiments',
        examples_group_attr='shape',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.04'),
        num_outputs_max=5,
        contents_per_hit=40,
        content_type_model=ShapeRectifiedNormalLabel,
        out_content_type_model=ShapeRectifiedNormalQuality,
        out_content_attr='rectified_normal',
        content_filter={
            'invalid': False,
            'shape__invalid': False,
            'shape__planar': True,
            #'shape__num_vertices__gte': 10,
            'shape__pixel_area__gt': 10 * Shape.MIN_PLANAR_AREA,
            #'automatic': True,
            #'shape__correct': True,
            #'shape__substance__isnull': False,
            #'shape__photo__whitebalanced': True,
            #'shape__photo__scene_category_correct': True,
        },
        title='Click on images that are correctly rotated',
        description='This task involves clicking on images that are correctly rotated.',
        keywords='material,substance,shape,image,picture,classify,label',
        #frame_height=7500,
        requirements={},
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
    )


def update_votes_cubam(show_progress=False):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task """

    from mturk.cubam import update_votes_cubam
    changed_objects = []

    changed_objects += update_votes_cubam(
        ShapeRectifiedNormalLabel,
        ShapeRectifiedNormalQuality.objects.filter(
            invalid=False, rectified_normal__invalid=False),
        'rectified_normal_id', 'correct', 'correct',
        score_threshold=0, min_votes=5,
        show_progress=show_progress,
        return_changed_objects=True,
        experiment_filter={'slug': 'quality_rectify'}
    )

    return changed_objects


def external_task_extra_context(slug, context):
    """ Add extra context for each task (called by
    ``mturk.views.external.external_task_GET``) """

    if slug == "rectify_vp":
        context['include_uvn_matrices'] = True

    elif slug == 'quality_rectify' or slug.startswith('rectify_'):
        context['html_yes'] = 'rectified'
        context['html_no'] = 'not rectified'
