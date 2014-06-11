from clint.textui import progress

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from photos.models import Photo, PhotoSceneCategory


class Command(BaseCommand):
    args = ''
    help = 'Temp fix'

    def handle(self, *args, **options):

        admin_user = User.objects.get_or_create(
            username='admin')[0].get_profile()
        scene_category, _ = PhotoSceneCategory.objects \
                .get_or_create(name='kitchen')

        for id in progress.bar(xrange(1, 37)):
            photo = Photo.objects.get(id=id)
            if not photo.scene_category:
                photo.scene_category = scene_category
            photo.scene_category_correct = True
            photo.save()
