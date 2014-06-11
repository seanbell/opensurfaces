from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from common.utils import progress_bar
from intrinsic.tasks import sample_intrinsic_points_task

from photos.models import PhotoLightStack

from intrinsic.models import IntrinsicPoint, IntrinsicPointComparison


class Command(BaseCommand):
    args = ''
    help = (
        'Sample intrinsic points for each light stack such that each photo '
        'has the same edges and points within each light stack'
    )

    def handle(self, *args, **options):

        # dense samoling:
        kwargs = {}
        kwargs['min_separation'] = Decimal('0.03')
        kwargs['avoid_existing_points'] = False
        kwargs['chromaticity_thresh'] = None

        with transaction.atomic():
            for light_stack in progress_bar(PhotoLightStack.objects.all()):
                photos = light_stack.photos.all()

                photo_id = photos[0].id

                # sample the new photo
                sample_intrinsic_points_task(
                    photo_id=photo_id, min_edges=1, **kwargs)

                # add points and edges
                points = list(
                    IntrinsicPoint.objects.filter(
                        photo_id=photo_id,
                        min_separation=kwargs['min_separation']
                    )
                )
                edges = list(
                    IntrinsicPointComparison.objects.filter(
                        photo_id=photo_id,
                        point1__min_separation=kwargs['min_separation'],
                        point2__min_separation=kwargs['min_separation'],
                    )
                )

                for photo in photos[1:]:
                    point_map = {}
                    for old in points:
                        # sample new color
                        rgb = photo.get_pixel(old.x, old.y, width='300')
                        sRGB = '%02x%02x%02x' % rgb
                        # copy old position
                        point_map[old.id] = IntrinsicPoint.objects.create(
                            photo=photo, x=old.x, y=old.y, sRGB=sRGB,
                            min_separation=old.min_separation,
                        )
                    for old in edges:
                        IntrinsicPointComparison.objects.create(
                            photo=photo,
                            point1=point_map[old.point1.id],
                            point2=point_map[old.point2.id],
                        )
