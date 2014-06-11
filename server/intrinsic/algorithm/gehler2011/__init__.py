import os
import shutil
import tempfile
import subprocess
from PIL import Image


def run(image, downsample=1, **kwargs):
    tmpdir = tempfile.mkdtemp()
    try:
        destdir = os.path.join(tmpdir, 'gehler2011')
        shutil.copytree(os.path.dirname(__file__), destdir)
        if downsample != 1:
            image = image.resize((image.size[0] / downsample, image.size[1] / downsample), Image.ANTIALIAS)
        image.save(os.path.join(destdir, 'data', 'input', 'diffuse.png'))

        subprocess.check_call(args=[
            'matlab', '-nodisplay', '-nosplash', '-nodesktop', '-r',
            'Exe; exit'
        ], cwd=os.path.join(destdir, 'src'))

        reflectance = Image.open(os.path.join(destdir, 'src', 'reflectance.png'))
        if downsample != 1:
            reflectance = reflectance.resize(
                (image.size[0], image.size[1]), Image.ANTIALIAS)
        return reflectance
    finally:
        shutil.rmtree(tmpdir)
