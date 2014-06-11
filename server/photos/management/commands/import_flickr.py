import os
from optparse import make_option

from clint.textui import progress

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from photos.models import PhotoSceneCategory, FlickrUser
from photos.add import add_photo
#from licenses.models import License


class Command(BaseCommand):
    args = '<flickr_dir>'
    help = 'Adds photos from flickr'

    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete photos after they are visited'),
    )

    def handle(self, *args, **options):
        admin_user = User.objects.get_or_create(
            username='admin')[0].get_profile()

        delete = bool(options['delete'])

        print 'Visiting: %s' % args[0]
        for root, dirs, files in os.walk(args[0]):
            print 'Visiting %s: %d files' % (root, len(files))

            # only create a category if has at least one photo
            scene_category = None

            num_added = 0
            for filename in progress.bar(files):
                if filename.endswith(".jpg"):
                    path = os.path.join(root, filename)

                    split = filename.rindex('_')
                    flickr_username = filename[:split]
                    flickr_id = filename[split + 1:filename.rindex('.')]
                    flickr_user = FlickrUser.objects.get_or_create(
                        username=flickr_username)[0]

                    #license = License.objects.get_or_create(
                        #user=user, name='CC BY-NC-SA 2.0')[0]

                    if not scene_category:
                        name = os.path.basename(root).replace('+', ' ')
                        scene_category, _ = PhotoSceneCategory.objects \
                            .get_or_create(name=name)

                    try:
                        add_photo(
                            path=path,
                            user=admin_user,
                            scene_category=scene_category,
                            flickr_user=flickr_user,
                            flickr_id=flickr_id,
                            license=None,
                            must_have_exif=True,
                            must_have_fov=True,
                        )
                    except Exception as e:
                        print '\nNot adding photo:', e
                    else:
                        print '\nAdded photo:', path
                        num_added += 1

                    if delete:
                        from common.tasks import os_remove_file
                        os_remove_file.delay(path)

            print 'Added %d photos to %s' % (num_added, root)
