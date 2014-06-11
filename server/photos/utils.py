import re
import math
import numbers
import subprocess
import numpy as np
import cStringIO as StringIO
import hashlib
from PIL import Image
from pilkit.utils import open_image
from photos.ccd_data import CCD_WIDTHS


def get_exif(path):
    """ Return a string containing the EXIF data from a JPEG using the
    ``jhead`` utility """
    try:
        # clean up lines and remove non-ascii characters.  there seems to be
        # some invalid unicode, which makes any code that uses this throw
        # exceptions.
        lines = subprocess.check_output(['jhead', path]).split('\n')
        kept_lines = []
        for line in lines:
            ascii = True
            for letter in line:
                if ord(letter) < 32 or ord(letter) > 127:
                    ascii = False
                    break
            if ascii:
                line = line.strip()
                if len(line) > 0:
                    line = re.sub(r"[ \t]+", " ", line)
                    kept_lines.append(line)

        return '\n'.join(kept_lines) if kept_lines else None
    except:
        return None

    #tags = {}
    #for k, v in exiftable.items():
        #ascii = True
        #if isinstance(v, str):
            #for letter in v:
                #if ord(letter) < 32 or ord(letter) > 127:
                    #ascii = False
                    #break

        ## only store ascii values
        #if ascii:
            #tags[TAGS.get(k, k)] = v

    #return tags


def get_fov(exif):
    """ Return the FOV (of the wider dimension) of a photo in degrees """

    lines = exif.split('\n')

    # get make and model
    make = None
    model = None
    ccd = None
    focal = None
    zoom = None
    for line in lines:
        if line.startswith("Camera model"):
            model = re.search(r":\s+(.*)$", line).group(1)
        elif line.startswith("Camera make"):
            make = re.search(r":\s+(.*)$", line).group(1)
        elif line.startswith("Focal length"):
            focal = float(re.search(r":\s+([0-9.]+)mm", line).group(1))
        #elif line.startswith("CCD width"):
            #ccd = float(re.search(r": ([0-9.]+)mm", line).group(1))
        elif line.startswith("Digital zoom"):
            zoom = float(re.search(r":\s+([0-9.]+)x", line).group(1))

    if not make or not model:
        return None

    if zoom and zoom > 0:
        focal *= zoom

    query = re.sub(r"\s+", " ", "%s %s" % (make, model)).lower()
    if query in CCD_WIDTHS:
        ccd = CCD_WIDTHS[query]

    if not ccd:
        return None

    if not isinstance(focal, numbers.Number):
        focal = float(focal[0]) / float(focal[1])

    return math.degrees(2 * math.atan(0.5 * ccd / focal))


def pil_to_numpy(pil):
    """ Convert an 8bit PIL image (0 to 255) to a floating-point numpy array
    (0.0 to 1.0) """
    return np.asarray(pil).astype(float) / 255.0


def numpy_to_pil(img):
    """ Convert a floating point numpy array (0.0 to 1.0) to an 8bit PIL image
    (0 to 255) """
    return Image.fromarray(
        np.clip(img * 255, 0, 255).astype(np.uint8)
    )


def hash_pil_image(pil):
    """ Compute the md5 hash of a PIL image """
    output = StringIO.StringIO()
    pil.save(output)
    return hashlib.md5(output.getvalue()).hexdigest()


def rgb_to_srgb(rgb):
    """ Convert an image from linear RGB to sRGB.

    :param rgb: numpy array in range (0.0 to 1.0)
    """
    ret = np.zeros_like(rgb)
    idx0 = rgb <= 0.0031308
    idx1 = rgb > 0.0031308
    ret[idx0] = rgb[idx0] * 12.92
    ret[idx1] = np.power(1.055 * rgb[idx1], 1.0 / 2.4) - 0.055
    return ret


def srgb_to_rgb(srgb):
    """ Convert an image from sRGB to linear RGB.

    :param srgb: numpy array in range (0.0 to 1.0)
    """
    ret = np.zeros_like(srgb)
    idx0 = srgb <= 0.04045
    idx1 = srgb > 0.04045
    ret[idx0] = srgb[idx0] / 12.92
    ret[idx1] = np.power((srgb[idx1] + 0.055) / 1.055, 2.4)
    return ret


def pil_srgb_to_rgb(pil):
    """ Convert a PIL image from sRGB to RGB """
    return numpy_to_pil(srgb_to_rgb(pil_to_numpy(pil)))
