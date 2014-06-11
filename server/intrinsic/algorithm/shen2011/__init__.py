import os
import glob
import shutil
import tempfile
import subprocess
from PIL import Image


def run(image, unmap_srgb, wd, rho, **kwargs):
    tmpdir = tempfile.mkdtemp()
    try:
        for f in glob.glob('%s/*.m' % os.path.dirname(__file__)):
            shutil.copy(f, os.path.join(tmpdir, os.path.basename(f)))

        image.save(os.path.join(tmpdir, 'input.png'))

        subprocess.check_call(args=[
            'matlab', '-nodisplay', '-nosplash', '-nodesktop', '-r',
            'unmap_srgb=%s; wd=%s; rho=%s; RunIntrinsicImage; exit' % (
                int(unmap_srgb), int(wd), float(rho),
            )
        ], cwd=tmpdir)

        return (Image.open(os.path.join(tmpdir, 'reflectance.png')),
                Image.open(os.path.join(tmpdir, 'shading.png')))
    finally:
        shutil.rmtree(tmpdir)
