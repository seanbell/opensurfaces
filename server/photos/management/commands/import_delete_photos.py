import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from common.utils import progress_bar
from photos.tasks import add_photo_task


class Command(BaseCommand):
    args = '<photo_directory>'
    help = 'Imports photos and deletes the original'

    def handle(self, *args, **options):
        if len(args) < 0:
            print "Usage: ./manage.py import_delete_photos <photo_directory>"

        admin_user = User.objects.get_or_create(username='admin')[0].profile

        print 'Visiting: %s' % args[0]
        for root, dirs, files in os.walk(args[0]):
            print 'Visiting %s: %d files' % (root, len(files))

            def sort_key(x):
                try:
                    return os.path.getsize(os.path.join(root, x))
                except OSError:
                    return 0

            print 'Sorting files by size...'
            files = sorted(files, key=sort_key, reverse=True)

            print 'Processing files...'
            num_added = 0
            for filename in progress_bar(files):
                filename_base, filename_ext = os.path.splitext(filename)
                if filename_ext.lower() == ".jpg":
                    path = os.path.join(root, filename)

                    add_photo_task.delay(
                        path=path,
                        user=admin_user,
                        scene_category=None,
                        must_have_exif=False,
                        must_have_fov=False,
                        delete_original=True,
                    )

            print 'Queued %d photos from %s' % (num_added, root)
