import os
import shutil
import tempfile
import subprocess
import numpy as np
from PIL import Image


def run(image, km_k, **kwargs):
    tmpdir = tempfile.mkdtemp()
    try:
        destdir = os.path.join(tmpdir, 'garces2012')
        shutil.copytree(os.path.dirname(__file__), destdir)

        for d in [os.path.join(destdir, 'examples'),
                  os.path.join(destdir, 'results', 'Kmeans')]:
            if not os.path.exists(d):
                os.makedirs(d)

        input_filename = os.path.join(destdir, 'examples', 'input.png')
        image.save(input_filename)

        subprocess.check_call(args=[
            os.path.join('intrinsic_code', 'build', 'release', 'garces2012'),
            '-i', input_filename, '-seg-mode', 'KMEANS', '-km-k', str(km_k)
        ], cwd=destdir)

        # convert to png
        output_base = os.path.join(destdir, 'results', 'Kmeans', 'input_k%s' % km_k)
        subprocess.check_call(args=[
            'convert', '%s_reflectance.ppm' % output_base, '%s_reflectance.png' % output_base
        ])
        subprocess.check_call(args=[
            'convert', '%s_shading.pgm' % output_base, '%s_shading.png' % output_base
        ])

        # load images and undo Garces' 1/2.2 mapping, so that we can re-map to
        # sRGB (as expected for the web).
        r = Image.open('%s_reflectance.png' % output_base)
        s = Image.open('%s_shading.png' % output_base)
        if kwargs['remap_gamma_2_2']:
            r, s = [np.power(np.asarray(x) / 255.0, 2.2) for x in (r, s)]
        return r, s
    finally:
        shutil.rmtree(tmpdir)
