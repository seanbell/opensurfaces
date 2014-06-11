from decimal import Decimal
from django.conf import settings

from common.utils import has_foreign_key

from photos.models import Photo, PhotoSceneQualityLabel, PhotoWhitebalanceLabel


def configure_experiments():
    """ This function is automatically called by
    the command ./manage.py mtconfigure """

    # must be imported locally to avoid a circular import
    from mturk.utils import configure_experiment

    # aliases
    sandbox = settings.MTURK_SANDBOX
    production = not sandbox

    configure_experiment(
        slug='quality_scene',
        template_dir='photos/experiments',
        module='photos.experiments',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.02'),
        num_outputs_max=5,
        contents_per_hit=50,
        content_type_model=Photo,
        out_content_type_model=PhotoSceneQualityLabel,
        out_content_attr='photo',
        content_filter='{}',
        title='Click on images that belong to a scene category',
        description='Given a collection of images, your job is to decide which images '
                    'belong to that scene category.',
        keywords='category,images,collection,image,picture,classify',
        #frame_height=8000,
        requirements={},
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
    )

    configure_experiment(
        slug='label_whitebalance',
        template_dir='photos/experiments',
        module='photos.experiments',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.05'),
        num_outputs_max=5,
        contents_per_hit=15 if production else 4,
        max_active_hits=50,
        content_type_model=Photo,
        out_content_type_model=PhotoWhitebalanceLabel,
        out_content_attr='photo',
        content_filter={
            'scene_category_correct': True,
            'num_shapes__gt': 0,
        },
        title='Click on white or gray things in images',
        description='Your task is to click on points in an image that are white or gray.',
        keywords='whitebalance,appearance,image,picture,label',
        requirements={
            'min_points': 3
        },
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
    )


def update_votes_cubam(show_progress=False):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task """

    from mturk.cubam import update_votes_cubam
    changed_objects = []

    changed_objects += update_votes_cubam(
        Photo, PhotoSceneQualityLabel.objects.filter(invalid=False),
        'photo_id', 'correct', 'scene_category_correct',
        quality_method_attr='scene_category_correct_method',
        score_threshold=0, min_votes=5,
        show_progress=show_progress,
        return_changed_objects=True,
        experiment_filter={'slug': 'quality_scene'}
    )

    changed_objects += update_votes_cubam(
        Photo, PhotoWhitebalanceLabel.objects.filter(invalid=False),
        'photo_id', 'whitebalanced', 'whitebalanced',
        score_threshold=0, min_votes=5,
        show_progress=show_progress, return_changed_objects=True,
        experiment_filter={'slug': 'label_whitebalance'}
    )

    return changed_objects


def update_changed_objects(changed_objects):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task
    with all objects that were changed by new votes.  """

    from photos.tasks import update_photos_num_shapes
    changed_photo_ids = [
        s.photo_id for s in changed_objects
        if has_foreign_key(s, 'photo')]
    update_photos_num_shapes(set(changed_photo_ids))


def external_task_extra_context(slug, context):
    """ Add extra context for each task (called by
    ``mturk.views.external.external_task_GET``) """

    if slug == 'quality_scene':
        scenes_dict = {}
        for c in context['contents']:
            sc = c.scene_category
            if sc.id in scenes_dict:
                scenes_dict[sc.id]['photos'].append(c)
            else:
                scenes_dict[sc.id] = {
                    'name': sc.name,
                    'description': sc.description,
                    'photos': [c]
                }
        # sort photos by aspect ratio
        scenes_list = scenes_dict.values()
        for scene in scenes_list:
            scene['photos'].sort(key=lambda p: -p.aspect_ratio)
        context['scenes'] = scenes_list
