import json
from decimal import Decimal
from collections import Counter

from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User
from accounts.models import UserProfile
from shapes.models import Shape, MaterialShape
from bsdfs.models import EnvironmentMap, ShapeBsdfLabel_wd, ShapeBsdfQuality


def configure_experiments():
    """ This function is automatically called by
    the command ./manage.py mtconfigure """

    # must be imported locally to avoid a circular import
    from mturk.utils import configure_experiment

    # aliases
    sandbox = settings.MTURK_SANDBOX
    production = not sandbox

    # set up envmaps
    envmap = EnvironmentMap.objects.get_or_create(
        user=User.objects.get_or_create(
            username='admin')[0].get_profile(),
        name='ennis')

    for envmap in EnvironmentMap.objects.all():
        configure_experiment(
            slug='bsdf_wd',
            template_dir='bsdfs/experiments',
            module='bsdfs.experiments',
            examples_group_attr='shape',
            variant={'envmap_id': envmap.id},
            version=1,  # 2: intrinsic images, 1: original opensurfaces
            reward=Decimal('0.10'),
            num_outputs_max=1,
            contents_per_hit=10,
            max_active_hits=2000,
            content_type_model=MaterialShape,
            out_content_type_model=ShapeBsdfLabel_wd,
            out_content_attr='shape',
            content_filter={
                #'synthetic': True,
                #'synthetic_slug__in': ['teapot', 'teacup', 'spoon', 'coyote'],
                'invalid': False,
                'pixel_area__gt': Shape.MIN_PIXEL_AREA,
                'num_vertices__gte': 10,
                'correct': True,
                'substance__isnull': False,
                'substance__fail': False,
                'photo__whitebalanced': True,
                'photo__scene_category_correct': True,
            },
            title='Adjust a blob to match an image',
            description='Looking at an image, your goal is to adjust the appearance '
                        'of a blob so that it matches a target photograph.  A modern '
                        'browser is required.',
            keywords='material,appearance,image,picture,classify,BRDF,microfacet,blob,appearance',
            frame_height=1150,
            requirements={},
            #qualifications='{ "bsdf_match": 1 }',
            auto_add_hits=False,  # settings.MTURK_SANDBOX,
        )

    for attr in ('color', 'gloss'):
        content_filter = {
            'invalid': False,
            'shape__invalid': False,
            'give_up': False,
            #'shape__pixel_area__gt': Shape.MIN_PIXEL_AREA,
            #'shape__correct': True,
            #'shape__substance__isnull': False,
            #'shape__substance__fail': False,
            #'shape__photo__whitebalanced': True,
            #'shape__photo__scene_category_correct': True,
        }
        if production and attr == 'gloss':
            content_filter['color_correct'] = True

        configure_experiment(
            slug='quality_bsdf_%s' % attr,
            template_dir='bsdfs/experiments',
            module='bsdfs.experiments',
            examples_group_attr='shape',
            variant={'bsdf_version': 'wd'},
            version=1,  # 2: intrinsic images, 1: original opensurfaces
            reward=Decimal('0.04'),
            num_outputs_max=5,
            contents_per_hit=40,
            content_type_model=ShapeBsdfLabel_wd,
            out_content_type_model=ShapeBsdfQuality,
            out_content_attr='shapebsdflabel_wd',
            content_filter=content_filter,
            title='Click on blobs that match an image (%s)' % attr,
            description='This task involves clicking on images that match a blob next to the image.',
            keywords='material,substance,shape,image,picture,classify,label,blob,match,appearance',
            #frame_height=7500,
            requirements={},
            auto_add_hits=False,  # settings.MTURK_SANDBOX,
        )


def update_votes_cubam(show_progress=False):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task """

    from mturk.cubam import update_votes_cubam

    changed_objects = []

    for bsdf_version in ('wd',):
        bsdf_ct = ContentType.objects.get(
            app_label="bsdfs", model="shapebsdflabel_%s" % bsdf_version)
        bsdf_model = bsdf_ct.model_class()

        # gloss
        changed_objects += update_votes_cubam(
            bsdf_model, ShapeBsdfQuality.objects.filter(
                invalid=False, content_type=bsdf_ct,
                gloss_correct__isnull=False),
            'object_id', 'gloss_correct', 'gloss_correct',
            score_threshold=0, min_votes=5,
            show_progress=show_progress,
            return_changed_objects=True,
            experiment_filter={
                'slug': 'quality_bsdf_gloss',
                'variant': json.dumps({'bsdf_version': bsdf_version}),
            }
        )

        # color
        changed_objects += update_votes_cubam(
            bsdf_model, ShapeBsdfQuality.objects.filter(
                invalid=False, content_type=bsdf_ct,
                color_correct__isnull=False),
            'object_id', 'color_correct', 'color_correct',
            score_threshold=0, min_votes=5,
            show_progress=show_progress,
            return_changed_objects=True,
            experiment_filter={
                'slug': 'quality_bsdf_color',
                'variant': json.dumps({'bsdf_version': bsdf_version}),
            }
        )

    return changed_objects


def update_changed_objects(changed_objects):
    """ This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task
    with all objects that were changed by new votes.  """

    pass


def external_task_extra_context(slug, context):
    """ Add extra context for each task (called by
    ``mturk.views.external.external_task_GET``) """

    if slug.startswith('bsdf'):
        context['html_yes'] = 'blob matches'
        context['html_no'] = 'blob does not match'

    elif slug.startswith('quality_bsdf_color'):
        context['html_yes'] = 'color matches'
        context['html_no'] = 'color does not match'

    elif slug.startswith('quality_bsdf_gloss'):
        context['html_yes'] = 'gloss matches'
        context['html_no'] = 'gloss does not match'


def configure_qualifications():
    from mturk.models import MtQualification, MtQualificationAssignment
    from mturk.utils import get_or_create_mturk_worker

    #
    # BSDF matching

    bsdfmatch = MtQualification.objects.get_or_create(
        slug="bsdf_match",
        defaults={
            'name': "Appearance Matching Master",
            'keywords': "appearance,matching,blob,graphics,BRDF",
            'description': "You are an expert at matching the appearance of a synthetic blob and a shape in an image."
        }
    )[0]

    good_users = dict(Counter(
        ShapeBsdfLabel_wd.objects
        .filter(color_correct=True, gloss_correct=True)
        .values_list('user__mturk_worker_id', flat=True)
    ).most_common())

    bad_users = dict(Counter(
        ShapeBsdfLabel_wd.objects
        .filter(Q(color_correct=False) | Q(gloss_correct=False))
        .values_list('user__mturk_worker_id', flat=True)
    ).most_common())

    for (id, ngood) in good_users.iteritems():
        nbad = bad_users[id] if id in bad_users else 0
        if ngood + nbad > 0:
            perc = float(ngood) / float(ngood + nbad)
        if ngood >= 30:
            worker = UserProfile.objects.get(mturk_worker_id=id)
            if perc >= 0.75:
                bsdfmatch_asst, created = bsdfmatch.assignments.get_or_create(
                    worker=worker)
                print 'Granting bsdf_match to %s (%s good, %s bad)' % (id, ngood, nbad)
                bsdfmatch_asst.set_value(1)
            elif perc < 0.1 and not worker.always_approve:
                # worker.block(reason=("For blob matching tasks, your accuracy is %s%%, which is too low.  " +
                                     #"Most workers have an accuracy above 75%%.") % int(perc * 100))
                print 'WOULD block user %s (%s good, %s bad, %s%%)' % (
                    worker.mturk_worker_id, ngood, nbad, perc * 100)
            elif perc < 0.5:
                try:
                    bsdfmatch.assignments.get(worker=worker).set_value(0)
                    print 'Revoking bsdf_match from %s (%s good, %s bad)' % (id, ngood, nbad)
                except MtQualificationAssignment.DoesNotExist:
                    pass
        elif nbad >= 30 and perc < 0.1 and not worker.always_approve:
            # worker.block(reason=("For blob matching tasks, your accuracy is %s%%, which is too low.  " +
                                 #"Most workers have an accuracy above 75%%.") % int(perc * 100))
            print 'WOULD block user %s (%s good, %s bad, %s%%)' % (
                worker.mturk_worker_id, ngood, nbad, perc * 100)

    #
    # Grant quals to admin

    if settings.MTURK_ADMIN_WORKER_ID:
        admin_user = get_or_create_mturk_worker(settings.MTURK_ADMIN_WORKER_ID)
        bsdfmatch.assignments.get_or_create(worker=admin_user)[0].set_value(1)
