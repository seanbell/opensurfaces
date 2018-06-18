import os
import subprocess
import traceback
from celery import shared_task

from imagekit.utils import open_image, save_image

from django.conf import settings
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from shapes.models import SubmittedShape, MaterialShape, ShapeSubstance

from shapes.utils import complex_polygon_area, \
    mask_complex_polygon, update_shape_image_pbox
from common.utils import save_obj_attr_image, get_content_tuple


@shared_task
def fill_in_bbox_task(shape):
    """ Helper to fill in the potentially empty image_bbox field """

    photo = shape.photo.__class__.objects.get(id=shape.photo.id)
    image_bbox = mask_complex_polygon(
        image=open_image(photo.image_orig),
        vertices=shape.vertices,
        triangles=shape.triangles,
        bbox_only=True)
    save_obj_attr_image(shape, attr='image_bbox',
                        img=image_bbox,
                        format='jpg', save=True)


@shared_task
def fill_in_pbox_task(shape):
    """ Helper to fill in the potentially empty image_pbox field """
    update_shape_image_pbox(shape, save=True)


@shared_task
def triangulate_submitted_shapes_task(photo, user, mturk_assignment,
                                      shape_model, submitted_shapes):
    """
    Given a list of input SubmittedShape instances, intersect them into
    non-overlapping complex polygons.  This is performed externally using the
    C++ "triangulate" program in the same repository.
    """

    try:
        triangulate_submitted_shapes_impl(
            photo, user, mturk_assignment, shape_model, submitted_shapes)
    except Exception as exc:
        # Re-add to the queue so that we don't lose tasks
        print 'Exception (%s) -- will retry in 5 minutes' % exc
        traceback.print_exc()
        raise triangulate_submitted_shapes_task.retry(
            exc=exc, countdown=60 * 5)


def triangulate_submitted_shapes_impl(
        photo, user, mturk_assignment, shape_model, submitted_shapes):

    if not submitted_shapes:
        return

    if not os.path.isfile(settings.TRIANGULATE_BIN):
        raise RuntimeError("ERROR: '%s' (settings.TRIANGULATE_BIN) does not exist -- "
                           "check that it is compiled" % settings.TRIANGULATE_BIN)

    input_lines = [('%s ' % s.id) + ' '.join(
        filter(None, s.vertices.split(','))) for s in submitted_shapes]
    input_txt = '\n'.join(input_lines) + '\nEND'

    process = None
    try:
        process = subprocess.Popen(
            args=settings.TRIANGULATE_BIN,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
        output_txt, errors_txt = process.communicate(input_txt)
    except:
        if process:
            process.kill()
            process.wait()
        raise

    if not output_txt:
        raise ValueError(
            "Error with triangulate.  Bin:%s\nInput:\n%s\n\nOutput:\n%s\n\nErrors:\n%s" % (
                settings.TRIANGULATE_BIN, input_txt, output_txt, errors_txt)
        )

    if errors_txt:
        print errors_txt

    #print("Bin:%s\nInput:\n%s\n\nOutput:\n%s\n\nErrors:\n%s" % (
        #settings.TRIANGULATE_BIN, input_txt, output_txt, errors_txt))

    new_content_tuples = []
    output_lines = output_txt.split('\n')

    with transaction.atomic():
        for line in output_lines:
            line = line.strip()
            if not line:
                continue

            fields = line.split('|')
            if len(fields) != 4:
                raise ValueError("Invalid output: %s" % repr(output_txt))

            ids = [int(f) for f in filter(None, fields[0].split(' '))]

            if not ids:
                print 'Discarding shape not contained in input'
                continue

            verts, tris, segs = [','.join(filter(None, f.split(' ')))
                                 for f in fields[1:4]]

            # compute polygon area and discard small polygons
            area = complex_polygon_area(verts, tris)
            # 0.0002 is roughly a 32x32 patch for a 2400x2400 image
            if area < 0.0001:
                print 'Discarding: verts: "%s", tris: "%s", segs: "%s", area: %s' % (
                    verts, tris, segs, area)
                continue

            # convert area to pixels
            pixel_area = area * photo.image_orig.width * \
                photo.image_orig.height

            # extract segmentation times
            time_ms_list = []
            ss_list = []
            for ss in submitted_shapes:
                if int(ss.id) in ids:
                    ss_list.append(ss)
                    time_ms_list.append(ss.time_ms)

            if not ss_list or not time_ms_list:
                print 'Discarding shape not mapping to input shapes'

            # use the average time of the submitted shapes
            time_ms = sum(time_ms_list) / float(len(time_ms_list))

            # when correct is NULL a HIT will check the quality
            quality_method = None
            correct = None

            # code like this can be used with pre-qualified workers
            # to automatically assign quality
            #if pixel_area >= 12000:
            #    from mturk.models import MtQualificationAssignment
            #    try:
            #        correct = bool(MtQualificationAssignment.objects.get(
            #            worker=user, qualification__slug="mat_seg").value)
            #        if correct:
            #            quality_method = 'Q'
            #    except MtQualificationAssignment.DoesNotExist:
            #        correct = False

            new_obj, created = shape_model.objects.get_or_create(
                photo=photo,
                user=user,
                mturk_assignment=mturk_assignment,
                vertices=verts,
                triangles=tris,
                segments=segs,
                area=area,
                pixel_area=pixel_area,
                time_ms=time_ms,
                defaults={
                    'added': ss_list[0].added,
                    'correct': correct,
                    'quality_method': quality_method,
                }
            )

            if created:
                for ss in ss_list:
                    new_obj.submitted_shapes.add(ss)
                new_content_tuples.append(get_content_tuple(new_obj))

        # these are created outside of the mturk view response, so we need to
        # manually add them to the pending objects queue
        # (imported here to avoid circular imports)
        for (ct_id, obj_id) in new_content_tuples:
            mturk_assignment.submitted_contents.get_or_create(
                content_type=ContentType.objects.get_for_id(ct_id),
                object_id=obj_id,
            )

    # update photo shape count synchronously
    from photos.tasks import update_photos_num_shapes
    update_photos_num_shapes([photo.id])
    new_content_tuples.append(get_content_tuple(photo))

    # new pending objects
    from mturk.tasks import add_pending_objects_task
    add_pending_objects_task.delay(new_content_tuples)


@shared_task
def retriangulate_material_shapes_task(photo):
    """
    DANGER ZONE: this DELETES all material shapes for this object and
    recomputes the triangulation for a material shape.  If multiple users
    submitted, it triangulates only the one with the most vertices and deletes
    the rest of the material shapes.
    """

    all_submitted_shapes = list(photo.submitted_shapes.all())
    if len(all_submitted_shapes) < 1:
        return

    # find common assignment and user
    mturk_assignments = set([s.mturk_assignment for s in all_submitted_shapes])
    if len(mturk_assignments) != 1:
        print 'more than one user submitted -- picking assignment with most vertices'
        max_verts = 0
        max_asst = None
        for asst in mturk_assignments:
            asst_ss = SubmittedShape.objects.filter(mturk_assignment=asst)
            verts = sum([ss.num_vertices for ss in asst_ss])
            if verts > max_verts:
                max_verts = verts
                max_asst = asst
        mturk_assignment = max_asst
    else:
        mturk_assignment = iter(mturk_assignments).next()

    # delete existing images
    for shape in photo.material_shapes.all():
        for f in shape._ik.spec_files:
            f.delete()

    # delete existing triangulated shapes
    photo.material_shapes.all().delete()

    # only triangulate this assignment's shapes
    submitted_shapes = SubmittedShape.objects.filter(
        mturk_assignment=mturk_assignment)
    user = mturk_assignment.worker

    # triangulate new ones
    # Note: have to call asynchronously since it could raise an
    # exception and retry
    triangulate_submitted_shapes_task.delay(
        photo, user, mturk_assignment, MaterialShape, submitted_shapes)


@shared_task
def update_shape_image_crop_task(shape):
    """ recompute the cropped image for a shape """

    # import here to avoid cycle
    from shapes.utils import update_shape_image_crop
    update_shape_image_crop(shape, save=True)


@shared_task
def save_substance_grid(substance_id, outdir, show_progress=False):
    try:
        os.makedirs(outdir)
    except OSError as e:
        print e

    substance = ShapeSubstance.objects.get(id=substance_id)
    print 'substance: %s' % substance
    qset = MaterialShape.objects.filter(
        substance_id=substance_id, photo__inappropriate=False)
    if not qset.exists():
        print 'no shapes for %s' % substance
        return

    from common.utils import create_image_grid_qset
    out = create_image_grid_qset(qset, 'image_square_300',
                                 ncols=20, size=300,
                                 max_qset_size=10 * 20 * 16 / 9,
                                 downsample_ratio=2,
                                 show_progress=show_progress)

    outname = os.path.join(outdir, substance.name
                           .replace(' - ', '-').replace(' ', '-')
                           .replace('/', '-').replace("'", '') + '.png')
    with open(outname, 'wb') as outfile:
        save_image(out, outfile, format="PNG")


@shared_task
def create_shape_image_sample_task(shape, sample_width=256, sample_height=256):
    from shapes.utils import create_shape_image_sample
    try:
        create_shape_image_sample(shape, sample_width, sample_height)
    except Exception as exc:
        # Re-add to the queue so that we don't lose tass
        print 'Exception (%s) -- will retry in 30 seconds' % exc
        traceback.print_exc()
        raise create_shape_image_sample_task.retry(
            exc=exc, countdown=30)
