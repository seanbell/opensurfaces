import os
import shutil
import tempfile
import subprocess
from PIL import Image
import numpy as np


def run(image, chrom_thresh, texture_patch_distance, texture_patch_variance, gamma, **kwargs):
    tmpdir = tempfile.mkdtemp()
    try:
        destdir = os.path.join(tmpdir, 'zhao2012')
        shutil.copytree(os.path.dirname(__file__), destdir)
        image.save(os.path.join(destdir, 'input.png'))

        args = [
            'bash', 'run.sh',
            'input.png',
            '-c', str(chrom_thresh),
            '-td', str(texture_patch_distance),
            '-tv', str(texture_patch_variance),
        ]

        if gamma:
            args.append('-gamma')

        subprocess.check_call(args=args, cwd=destdir)

        r = Image.open(os.path.join(destdir, 'input_RI', 'input_ref_RI.png'))
        s = Image.open(os.path.join(destdir, 'input_RI', 'input_sd_RI.png'))

        if gamma:
            r, s = [np.power(np.asarray(x) / 255.0, 2.2) for x in (r, s)]

        return r, s
    finally:
        shutil.rmtree(tmpdir)
