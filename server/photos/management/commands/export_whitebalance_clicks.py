import numpy as np
from clint.textui import progress

from django.core.management.base import BaseCommand
from django.db.models import F
from imagekit.utils import open_image

from photos.models import PhotoWhitebalanceLabel
from photos.tasks import detect_vanishing_points


class Command(BaseCommand):
    args = ''
    help = 'Export the pixel colors of white clicks'

    def handle(self, *args, **options):
        qset = PhotoWhitebalanceLabel.objects.filter(
            whitebalanced=F('photo__whitebalanced')
        )

        out = []
        for label in progress.bar(qset):
            photo = label.photo.__class__.objects.get(id=label.photo.id)
            pil = open_image(photo.image_300)
            points_list = label.points.split(',')
            for idx in xrange(label.num_points):
                x = float(points_list[idx * 2]) * pil.size[0]
                y = float(points_list[idx * 2 + 1]) * pil.size[1]
                rgb = pil.getpixel((x, y))
                out.append([c / 255.0 for c in rgb])

        out = np.array(out)
        np.save(args[0] if args else 'whitebalance_clicks.npy', out)
