import os
import pywt
import functools

from PIL import Image
from clint.textui import progress
from multiprocessing import Pool

from django.core.management.base import BaseCommand

from shapes.models import ShapeImageSample
from common.wavelets import compute_wavelet_feature_vector


class Command(BaseCommand):
    args = ""
    help = "Creates features for classification"

    def handle(self, *args, **options):
        substance_names = [
            'Painted', 'Wood', 'Fabric/cloth', 'Tile', 'Metal', 'Carpet/rug',
            'Ceramic', 'Leather', 'Food', 'Brick', 'Stone', 'Skin'
        ]

        try:
             os.makedirs('svm')
        except Exception as e:
            print e

        all_samples = ShapeImageSample.objects.filter(
            shape__substance__name__in=substance_names
        ).order_by('?')

        train = []
        test = []

        # split training and testing
        print 'splitting training/test...'
        users = all_samples.distinct('shape__photo__flickr_user').values_list('shape__photo__flickr_user', flat=True).order_by()
        for u in progress.bar(users):
            if len(test) > len(train):
                train += all_samples.filter(shape__photo__flickr_user_id=u)
            else:
                test += all_samples.filter(shape__photo__flickr_user_id=u)

        print 'train size: %s' % len(train)
        print 'test size: %s' % len(test)

        for wavelet in progress.bar(pywt.wavelist('db') + pywt.wavelist('haar')):
            for training in [True, False]:
                print 'features for %s (training=%s)...' % (wavelet, training)

                cur_samples = train if training else test
                image_paths = [s.image.path for s in cur_samples]

                p = Pool(32)
                features = p.map(functools.partial(compute_features, wavelet), image_paths)
                p.close()

                with open('svm/%s-%s.svm' % (wavelet, 'train' if training else 'test'), 'w') as outfile:
                    for i_s, s in enumerate(cur_samples):
                        class_str = substance_names.index(s.shape.substance.name)
                        feature_str = ' '.join(['%s:%s' % (i_f+1, f) for (i_f, f) in enumerate(features[i_s])])
                        print >>outfile, class_str, feature_str


def compute_features(wavelet, img):
    return compute_wavelet_feature_vector(Image.open(img), wavelet=wavelet)
