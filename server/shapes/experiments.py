import json
from decimal import Decimal
from collections import Counter

from django.conf import settings
from common.utils import has_foreign_key

from accounts.models import UserProfile
from photos.models import Photo
from shapes.models import Shape, SubmittedShape, MaterialShape, MaterialShapeQuality, \
    ShapePlanarityLabel, ShapeSubstanceLabel, MaterialShapeNameLabel, ShapeSubstanceGroup, \
    ShapeSubstance, ShapeName


def configure_experiments():
    """ This function is automatically called by
    the command ./manage.py mtconfigure """

    # must be imported locally to avoid a circular import
    from mturk.utils import configure_experiment

    # aliases
    sandbox = settings.MTURK_SANDBOX
    production = not sandbox

    configure_experiment(
        slug='segment_material',
        template_dir='shapes/experiments',
        module='shapes.experiments',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.12'),
        num_outputs_max=6,
        out_count_ratio=6,
        contents_per_hit=1,
        max_active_hits=200,
        content_type_model=Photo,
        out_content_type_model=SubmittedShape,
        out_content_attr='photo',
        content_filter={
            'scene_category_correct': True,
            'license__creative_commons': True,
            'license__cc_no_deriv': False,
        },
        duration=60 * 60 * 3,
        title='Draw shapes in images',
        description='Draw polygons around regions that have the same material in a photograph.',
        keywords='material,substance,polygon,shape,draw,image,picture,classify',
        requirements={
            'min_shapes': 6,
            'min_vertices': 3
        },
        qualifications='{ "mat_seg": 1 }',
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
    )

    configure_experiment(
        slug='quality_material',
        template_dir='shapes/experiments',
        module='shapes.experiments',
        examples_group_attr='shape',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.04'),
        num_outputs_max=5 if production else 10,
        contents_per_hit=40,
        content_type_model=MaterialShape,
        out_content_attr='shape',
        out_content_type_model=MaterialShapeQuality,
        content_filter={
            'invalid': False,
            'correct__isnull': True,
            'pixel_area__gt': Shape.MIN_PIXEL_AREA,
            'photo__whitebalanced': True,
            'photo__scene_category_correct': True,
        },
        title='Click on images that contain a single material',
        description='This task involves clicking on images that contain a single type of material or texture within a red boundary.',
        keywords='material,substance,shape,image,picture,classify,label',
        requirements={},
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
        #examples_good=MaterialShape.objects.filter(
        #qualities__user=examples_user,
        #qualities__correct=True).order_by('?')[:200],
        #examples_bad=MaterialShape.objects.filter(
        #qualities__user=examples_user,
        #qualities__correct=False).order_by('?')[:200],
    )

    configure_experiment(
        slug='label_substance',
        template_dir='shapes/experiments',
        module='shapes.experiments',
        examples_group_attr='shape',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.10'),
        num_outputs_max=5,
        min_output_consensus=3,
        contents_per_hit=40,
        #max_active_hits=200,
        content_type_model=MaterialShape,
        out_content_type_model=ShapeSubstanceLabel,
        out_content_attr='shape',
        content_filter={
            'invalid': False,
            'correct': True,
            'pixel_area__gt': Shape.MIN_PIXEL_AREA,
            'num_vertices__gte': 4,
            #'photo__whitebalanced': True,
            'photo__scene_category_correct': True,
        },
        title='Click on the name of a material in an image',
        description='Given a shape highlighted in an image, select its material from a list.',
        keywords='material,substance,appearance,image,picture,classify',
        frame_height=1200,
        requirements={},
        #qualifications='{ "substance": 1 }',
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
    )

    configure_experiment(
        slug='label_planarity',
        template_dir='shapes/experiments',
        module='shapes.experiments',
        examples_group_attr='shape',
        version=1,  # 2: intrinsic images, 1: original opensurfaces
        reward=Decimal('0.04'),
        num_outputs_max=5 if production else 10,
        contents_per_hit=40,
        content_type_model=MaterialShape,
        out_content_type_model=ShapePlanarityLabel,
        out_content_attr='shape',
        content_filter={
            'invalid': False,
            'pixel_area__gt': Shape.MIN_PLANAR_AREA,
            'correct': True,
            'substance__isnull': False,
            'substance__fail': False,
            'num_vertices__gte': 4,
            #'photo__whitebalanced': True,
            'photo__scene_category_correct': True,
        },
        title='Click on images of planar objects',
        description='Your task is to select the planar objects out of a collection of images.',
        keywords='flat,planar,appearance,polygon,shape,draw,image,picture,classify,label',
        #frame_height=7500,
        requirements={},
        auto_add_hits=False,  # settings.MTURK_SANDBOX,
        #examples_good=MaterialShape.objects.filter(
        #planarities__user=examples_user,
        #planarities__planar=True).order_by('?')[:200],
        #examples_bad=MaterialShape.objects.filter(
        #planarities__user=examples_user,
        #planarities__planar=False).order_by('?')[:200],
    )

    for group in ShapeSubstanceGroup.objects.filter(active=True):
        configure_experiment(
            slug='label_name',
            template_dir='shapes/experiments',
            module='shapes.experiments',
            examples_group_attr='shape',
            variant=json.dumps({'substance_group_id': group.id}),
            completed_id='label_name',
            version=1,  # 2: intrinsic images, 1: original opensurfaces
            reward=Decimal('0.10'),
            num_outputs_max=5,
            min_output_consensus=3,
            contents_per_hit=50,
            content_type_model=MaterialShape,
            out_content_type_model=MaterialShapeNameLabel,
            out_content_attr='shape',
            content_filter={
                'invalid': False,
                'pixel_area__gt': Shape.MIN_PIXEL_AREA,
                'correct': True,
                'substance__isnull': False,
                'substance__group_id': group.id,
                'photo__scene_category_correct': True,
                'num_vertices__gte': 4,
                #'photo__scene_category__name': 'kitchen',
            },
            frame_height=1200,
            title='Click on the name of an object in an image',
            description='Given an object highlighted in an image, select its common English name from a list. (id: %s)' % group.id,
            keywords='object,categorize,appearance,image,picture,classify',
            requirements={},
            #qualifications='{ "substance": 1 }',
            auto_add_hits=False,  # settings.MTURK_SANDBOX,  # TODO: get rid of fixed list
        )


def update_votes_cubam(show_progress=False):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task """

    from mturk.cubam import update_votes_cubam
    changed_objects = []

    changed_objects += update_votes_cubam(
        MaterialShape, ShapePlanarityLabel.objects.filter(
            invalid=False, shape__invalid=False),
        'shape_id', 'planar', 'planar', quality_method_attr='planar_method',
        score_threshold=0, min_votes=5,
        show_progress=show_progress,
        return_changed_objects=True,
        experiment_filter={'slug': 'label_planarity'}
    )

    changed_objects += update_votes_cubam(
        MaterialShape, MaterialShapeQuality.objects.filter(
            invalid=False, shape__invalid=False),
        'shape_id', 'correct', 'correct',
        score_threshold=0, min_votes=5,
        show_progress=show_progress,
        return_changed_objects=True,
        experiment_filter={'slug': 'quality_material'}
    )

    return changed_objects


def update_changed_objects(changed_objects):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task
    with all objects that were changed by new votes.  """

    # update shape entropy
    updated_shape_ids = set()
    for o in changed_objects:
        if has_foreign_key(o, 'shape'):
            if o.shape_id not in updated_shape_ids:
                updated_shape_ids.add(o.shape_id)
                o.shape.update_entropy()


def external_task_extra_context(slug, context):
    """ Add extra context for each task (called by
    ``mturk.views.external.external_task_GET``) """

    if slug == 'quality_material':
        context['html_yes'] = 'one texture and tight boundary'
        context['html_no'] = 'multiple textures or bad boundary'

    elif slug == "label_substance":
        context['descriptions'] = ShapeSubstance.objects \
            .filter(representative_shape__isnull=False) \
            .select_related('representative_shape')
        context['failures'] = [
            "Not on list", "More than one material", "I can't tell"]
        context['categories'] = ShapeSubstance.objects \
            .filter(active=True, fail=False) \
            .order_by('name') \
            .values_list('name', flat=True)

    elif slug == "label_name":
        context['failures'] = [
            "Not on list", "More than one object", "I can't tell"]
        substance_group_id = context['variant']['substance_group_id']
        context['categories'] = ShapeName.objects \
            .filter(substance_groups=substance_group_id) \
            .order_by('name') \
            .values_list('name', flat=True)

    elif slug == "label_planarity":
        context['html_yes'] = 'planar'
        context['html_no'] = 'not planar'


def configure_qualifications():
    from mturk.models import MtQualification, MtQualificationAssignment
    from mturk.utils import get_or_create_mturk_worker

    #
    # Substance Labeling

    substance = MtQualification.objects.get_or_create(
        slug="substance",
        defaults={
            'name': "Material Naming Master",
            'keywords': "material,naming,substance,images",
            'description': "You are an expert at naming and identifying regions of material or texture in an image.",
        }
    )[0]

    shape_substance_labels = dict(
        MaterialShape.objects.filter(substance__isnull=False).values_list('id', 'substance_id'))
    shape_name_labels = dict(
        MaterialShape.objects.filter(name__isnull=False).values_list('id', 'name_id'))

    for worker in UserProfile.objects.exclude(mturk_worker_id=''):
        worker_substance_labels = ShapeSubstanceLabel.objects.filter(user=worker) \
            .values_list('shape_id', 'substance_id')
        worker_name_labels = MaterialShapeNameLabel.objects.filter(user=worker) \
            .values_list('shape_id', 'name_id')

        ngood = 0
        nbad = 0
        for (shape_id, worker_substance_label) in worker_substance_labels:
            if shape_id in shape_substance_labels:
                if worker_substance_label == shape_substance_labels[shape_id]:
                    ngood += 1
                else:
                    nbad += 1
        for (shape_id, worker_name_label) in worker_name_labels:
            if shape_id in shape_name_labels:
                if worker_name_label == shape_name_labels[shape_id]:
                    ngood += 1
                else:
                    nbad += 1

        if ngood + nbad > 0:
            perc = float(ngood) / float(ngood + nbad)

        if ngood >= 100:
            if perc >= 0.85:
                substance_asst, created = substance.assignments.get_or_create(
                    worker=worker)
                print 'Granting substance to %s (%s good, %s bad, %s%%)' % (
                    worker.mturk_worker_id, ngood, nbad, perc * 100)
                substance_asst.set_value(1)
            elif ngood + nbad >= 200 and perc < 0.75:
                try:
                    substance.assignments.get(worker=worker).set_value(0)
                    print 'Revoking substance from %s (%s good, %s bad, %s%%)' % (
                        worker.mturk_worker_id, ngood, nbad, perc * 100)
                except MtQualificationAssignment.DoesNotExist:
                    pass
                if perc < 0.75 and not worker.always_approve:
                    worker.block(reason=("For naming tasks, your accuracy is %s%%, which is too low.  " +
                                 "Most workers have an accuracy above 85%%.") % int(perc * 100))
                    print 'Blocking user %s (%s good, %s bad, %s%%)' % (
                        worker.mturk_worker_id, ngood, nbad, perc * 100)
        elif nbad >= 100 and not worker.always_approve:
            worker.block(reason=("For naming tasks, your accuracy is %s%%, which is too low.  " +
                                 "Most workers have an accuracy above 85%%.") % int(perc * 100))
            print 'Blocking user %s (%s good, %s bad, %s%%)' % (
                worker.mturk_worker_id, ngood, nbad, perc * 100)

    #
    # Material Segmentation

    matseg = MtQualification.objects.get_or_create(
        slug="mat_seg",
        defaults={
            'name': "Material Segmentation Master",
            'keywords': "material,segmentation,drawing,images",
            'description': "You are an expert at drawing and identifying regions of a single type of material or texture in an image.",
        }
    )[0]

    # adequate work but annoying to deal with
    matseg.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A1YLO4LT02D2F0'))[0].set_value(0)
    matseg.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='AU8FIYQPHKD7I'))[0].set_value(0)
    matseg.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A26GDUUFGPAYUL'))[0].set_value(0)
    matseg.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A2428ZTX6LJU33'))[0].set_value(0)
    matseg.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A2DHCVFGQRKU5'))[0].set_value(0)

    # great workers
    matseg.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A3LNPBZXHKKAA7'))[0].set_value(1)
    matseg.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A1ENHFQSXOXG6I'))[0].set_value(1)

    good_users = dict(Counter(
        MaterialShape.objects
        .filter(correct=True)
        .values_list('user__mturk_worker_id', flat=True)
    ).most_common())

    bad_users = dict(Counter(
        MaterialShape.objects
        .filter(correct=False)
        .values_list('user__mturk_worker_id', flat=True)
    ).most_common())

    for (id, ngood) in good_users.iteritems():
        if ngood > 50:
            nbad = bad_users[id] if id in bad_users else 0
            perc = float(ngood) / float(ngood + nbad)
            if perc >= 0.8:
                worker = UserProfile.objects.get(mturk_worker_id=id)
                matseg_asst, created = matseg.assignments.get_or_create(
                    worker=worker)
                if created or matseg_asst.value != 0:
                    print 'Granting mat_seg to %s (%s good, %s bad, %s%%)' % (id, ngood, nbad, perc * 100)
                    matseg_asst.set_value(1)
            elif perc < 0.6 and not worker.always_approve:
                worker = UserProfile.objects.get(mturk_worker_id=id)
                try:
                    matseg.assignments.get(worker=worker).set_value(0)
                    print 'Revoking mat_seg from %s (%s good, %s bad, %s%%)' % (id, ngood, nbad, perc * 100)
                except MtQualificationAssignment.DoesNotExist:
                    pass

    # Best workers

    matseg2 = MtQualification.objects.get_or_create(
        slug="mat_seg2",
        defaults={
            'name': "Material Segmentation Master 2",
            'keywords': "material,segmentation,drawing,images,2",
            'description': "You are a super expert at drawing and identifying regions of a single type of material or texture in an image.",
        }

    )[0]
    matseg2.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A3LNPBZXHKKAA7'))[0].set_value(1)
    matseg2.assignments.get_or_create(worker=UserProfile.objects.get(
        mturk_worker_id='A1ENHFQSXOXG6I'))[0].set_value(1)

    #
    # Grant quals to admin

    if settings.MTURK_ADMIN_WORKER_ID:
        admin_user = get_or_create_mturk_worker(settings.MTURK_ADMIN_WORKER_ID)
        matseg.assignments.get_or_create(worker=admin_user)[0].set_value(1)
        matseg2.assignments.get_or_create(worker=admin_user)[0].set_value(1)
        substance.assignments.get_or_create(worker=admin_user)[0].set_value(1)
