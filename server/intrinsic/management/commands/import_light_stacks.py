import os
import glob
from django.core.management.base import BaseCommand
from django.db import transaction

from common.utils import progress_bar
from photos.add import add_photo
from intrinsic.tasks import sample_intrinsic_points_task

from django.contrib.auth.models import User
from photos.models import PhotoSceneCategory, PhotoLightStack

from intrinsic.models import IntrinsicPoint, IntrinsicPointComparison


class Command(BaseCommand):
    args = ''
    help = 'Import photos of static scenes with multiple lighting conditions'

    def handle(self, *args, **options):
        admin_user = User.objects.get_or_create(
            username='admin')[0].get_profile()

        with transaction.atomic():
            for root in progress_bar(glob.glob('%s/*' % args[0])):
                slug = os.path.basename(root)
                print slug

                if 'janivar50' in slug or 'kitchen' in slug:
                    scene_category = PhotoSceneCategory.objects.get(
                        name='kitchen')
                elif 'mike_indoor' in slug or 'sofas' in slug:
                    scene_category = PhotoSceneCategory.objects.get(
                        name='living room')
                else:
                    raise ValueError("Unknown")

                light_stack = PhotoLightStack.objects.create(slug=slug)

                files = glob.glob('%s/*' % root)
                photos = [
                    add_photo(
                        path=f,
                        user=admin_user,
                        scene_category=scene_category,
                        light_stack=light_stack,
                    )
                    for f in files
                ]
