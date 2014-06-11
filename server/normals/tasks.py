import os
import json
from celery import shared_task

from imagekit.utils import save_image

from django.contrib.auth.models import User
from django.db.models import F

from shapes.models import MaterialShape
from normals.models import ShapeRectifiedNormalLabel

from common.utils import get_content_tuple


@shared_task
def orthogonalize_rectified_normal(id):
    """ Re-orthogonalizes the uvnb matrix for a rectified normal """
    rectified_normal = ShapeRectifiedNormalLabel.objects.get(id=id)
    rectified_normal.image_rectified = ''
    rectified_normal.orthogonalize(save=True)


@shared_task
def auto_rectify_shape(shape_id):
    """ Attempt to automatically rectify the shape based on vanishing points """

    if ShapeRectifiedNormalLabel.objects.filter(shape_id=shape_id, automatic=True).exists():
        print "shape already automatically rectified"
        return

    shape = MaterialShape.objects.get(id=shape_id)

    from normals.perspective import estimate_uvnb_from_vanishing_points
    uvnb, method, num_vanishing_lines = estimate_uvnb_from_vanishing_points(
        shape)
    if not uvnb:
        print "Could not estimate uvnb matrix"
        return

    admin_user = User.objects.get_or_create(
        username='admin')[0].get_profile()

    print 'method: %s, uvnb: %s' % (method, uvnb)
    obj = ShapeRectifiedNormalLabel.objects.create(
        user=admin_user,
        shape=shape,
        uvnb=json.dumps(uvnb),
        automatic=True,
        method=method,
        num_vanishing_lines=num_vanishing_lines
    )

    from mturk.tasks import add_pending_objects_task
    add_pending_objects_task.delay([get_content_tuple(obj)])


@shared_task
def save_texture_grid(outdir, max_qset_size=None, ncols=25, show_progress=False, category=None):
    try:
        os.makedirs(outdir)
    except OSError as e:
        print e

    qset = ShapeRectifiedNormalLabel.objects \
        .filter(shape__photo__license__publishable=True,
                shape__correct=True, shape__planar=True,
                shape__rectified_normal_id=F('id')) \
        .order_by('-shape__num_vertices')

    if category:
        qset = qset.filter(shape__substance__name=category)

    if not qset.exists():
        print 'no textures found'
        return

    if max_qset_size:
        qset = qset[:max_qset_size]

    from common.utils import create_image_grid_qset
    out = create_image_grid_qset(qset, 'image_rectified_square_300',
                                 ncols=ncols, size=256,
                                 downsample_ratio=1,
                                 show_progress=show_progress)

    if category:
        outname = os.path.join(outdir, '%s.png' % category.lower())
    else:
        outname = os.path.join(outdir, 'textures.png')
    with open(outname, 'wb') as outfile:
        save_image(out, outfile, format="PNG")
