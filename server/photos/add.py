import os

from django.core.files.images import ImageFile
from django.db import transaction

from photos.models import Photo
from licenses.models import License

from photos.utils import get_exif, get_fov
from common.utils import md5sum, get_content_tuple


def add_photo(path, must_have_fov=False, must_have_exif=False, **args):
    """ Add a photo to the database """

    if not os.path.exists(path):
        raise ValueError("File does not exist")

    if 'license' not in args:
        args['license'] = License.objects.get_or_create(
            name='All Rights Reserved')[0]

    # md5: check for duplicates
    md5 = md5sum(path)
    duplicate = True
    try:
        photo = Photo.objects.get(md5=md5)
    except Photo.DoesNotExist:
        duplicate = False
    except Photo.MultipleObjectsReturned:
        duplicates = Photo.objects.filter(md5=md5).order_by('id')
        for d in duplicates[1:]:
            d.delete()
    if duplicate:
        raise ValueError("Duplicate photo import: '%s'" % path)

    # parse exif
    if 'exif' not in args:
        print 'Obtaining EXIF...'
        exif = get_exif(path)
        if exif:
            args['exif'] = exif
        elif must_have_exif:
            raise ValueError("Photo has no EXIF: %s" % path)

    if 'fov' not in args:
        print 'Obtaining FOV...'
        fov = get_fov(args['exif'])
        if fov:
            args['fov'] = fov
        elif must_have_fov:
            raise ValueError("Could not obtain photo FOV: %s" % path)

    photo = None

    # use a transaction so that it is only committed to the database
    # after save() returns.  otherwise, there's a small time betwee
    # when the photo is added and it has an image attached.
    with transaction.atomic():
        with open(path, 'rb') as f:
            print 'Uploading photo...'
            photo = Photo.objects.create(
                image_orig=ImageFile(f),
                md5=md5,
                **args
            )

    from mturk.tasks import add_pending_objects_task
    add_pending_objects_task.delay([get_content_tuple(photo)])

    return photo
