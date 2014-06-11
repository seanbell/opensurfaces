from celery import shared_task

from django.conf import settings
from django.db.models import Sum
from django.core.cache import get_cache

from photos.models import Photo
from shapes.models import MaterialShape
from normals.models import ShapeRectifiedNormalLabel
from bsdfs.models import ShapeBsdfLabel_wd
from mturk.models import MtAssignment, MtSubmittedContent
from intrinsic.models import IntrinsicPointComparison
from common.utils import dict_union


@shared_task
def update_index_context_task():

    data = {
        'num_scenes_good': Photo.objects.filter(**Photo.DEFAULT_FILTERS).count(),
        'num_scenes_all': Photo.objects.all().count(),

        'num_whitebalanced_good': Photo.objects.filter(whitebalanced=True, scene_category_correct=True).count(),
        'num_whitebalanced_all': Photo.objects.filter(whitebalanced_score__isnull=False, scene_category_correct=True).count(),

        'num_shapes_good': MaterialShape.objects.filter(**MaterialShape.DEFAULT_FILTERS).count(),
        'num_shapes_all': MaterialShape.objects.filter().count(),

        'num_substances_good': MaterialShape.objects.filter(**dict_union({'substance__fail': False}, MaterialShape.DEFAULT_FILTERS)).count(),
        'num_substances_all': MaterialShape.objects.filter(**dict_union({'substance_entropy__isnull': False}, MaterialShape.DEFAULT_FILTERS)).count(),

        'num_planar_good': MaterialShape.objects.filter(**dict_union({'planar': True}, MaterialShape.DEFAULT_FILTERS)).count(),
        'num_planar_all': MaterialShape.objects.filter(**MaterialShape.DEFAULT_FILTERS).count(),

        'num_names_good': MaterialShape.objects.filter(**dict_union({'name__fail': False}, MaterialShape.DEFAULT_FILTERS)).count(),
        'num_names_all': MaterialShape.objects.filter(**dict_union({'name_entropy__isnull': False}, MaterialShape.DEFAULT_FILTERS)).count(),

        'num_textures_good': MaterialShape.objects.filter(rectified_normal__isnull=False, planar=True, correct=True).count(),
        'num_textures_all': ShapeRectifiedNormalLabel.objects.distinct('shape').count(),

        'num_bsdfs_good': MaterialShape.objects.filter(bsdf_wd__isnull=False).count(),
        'num_bsdfs_all': ShapeBsdfLabel_wd.objects.all().distinct('shape').count(),

        'num_judgements_all': IntrinsicPointComparison.objects.all().count(),

        'num_assignments_good': MtAssignment.objects.filter(hit__sandbox=False, status='A').count(),
        'num_assignments_all': MtAssignment.objects.filter(hit__sandbox=False, status__isnull=False).count(),

        'num_submitted_all': MtSubmittedContent.objects.filter(assignment__hit__sandbox=False).count(),

        'num_users_good': MtAssignment.objects.filter(hit__sandbox=False, status__isnull=False, worker__blocked=False).distinct('worker').count(),
        'num_users_all': MtAssignment.objects.filter(hit__sandbox=False, status__isnull=False).distinct('worker').count(),

        'num_hours_all': MtAssignment.objects.filter(hit__sandbox=False).aggregate(s=Sum('time_ms'))['s'] / 3600000,
    }

    if settings.ENABLE_CACHING:
        get_cache('persistent').set('home.index_context', data, timeout=None)
    return data
