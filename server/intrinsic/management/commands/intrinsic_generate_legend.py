from django.core.management.base import BaseCommand

import numpy as np
from photos.utils import numpy_to_pil
from colormath.color_objects import LabColor


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):
        height = 16
        bar = np.zeros((256, height, 3))

        for i in xrange(256):
            t = i / 255.0
            lab0 = np.array([40, 30, -70])
            lab1 = np.array([70, 30, 70])
            lab = t * lab0 + (1 - t) * lab1
            rgb = np.clip(LabColor(*lab).convert_to('rgb').get_value_tuple(), 0, 255)
            for j in xrange(height):
                bar[i, j, :] = rgb / 255.0

        image = numpy_to_pil(bar)
        image.save('bar.png')
        print "Saved to bar.png"
