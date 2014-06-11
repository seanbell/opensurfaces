from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from photos.models import PhotoSceneCategory
from photos.add import add_photo
#from licenses.models import License


class Command(BaseCommand):
    args = '<flickr_dir>'
    help = 'Adds photos from flickr'

    def handle(self, *args, **options):
        admin_user = User.objects.get_or_create(
            username='admin')[0].get_profile()
        print 'user:', admin_user

        name = 'kitchen'
        scene_category, _ = PhotoSceneCategory.objects \
            .get_or_create(name=name)

        path = args[0]
        if not path:
            print 'No path'
            return

        try:
            photo = add_photo(
                path=path,
                user=admin_user,
                scene_category=scene_category,
                flickr_user=None,
                flickr_id=None,
                license=None,
                exif='',
                fov=None,
            )
        except Exception as e:
            print '\nNot adding photo:', e
        else:
            print '\nAdded photo:', path
            photo.synthetic = True
            photo.save()
