import OpenEXR
import Imath
import numpy as np
from scipy.optimize import brute

from pilkit.processors import ResizeToFit

from intrinsic.models import IntrinsicSyntheticDecomposition, IntrinsicPoint, IntrinsicPointComparison
from photos.utils import rgb_to_srgb, numpy_to_pil
from common.utils import progress_bar


# The 14 layers we expect to find in a Multilayer OpenEXR file
LAYER_CHANNELS = {
    'depth': ['RenderLayer.Depth.%s' % c for c in 'ZZZ'],
    'normal': ['RenderLayer.Normal.%s' % c for c in 'XYZ'],
}
for a in ['Combined', 'Emit', 'Env']:
    LAYER_CHANNELS[a.lower()] = ['RenderLayer.%s.%s' % (a, c) for c in 'RGB']
for a in ['Gloss', 'Diff', 'Trans']:
    for b in ['Dir', 'Ind', 'Col']:
        LAYER_CHANNELS['%s_%s' % (a.lower(), b.lower())] = [
            'RenderLayer.%s%s.%s' % (a, b, c) for c in 'RGB'
        ]


def open_multilayer_exr(filename, tonemap=False, thumb_size=0, show_progress=False):
    """
    Load a multilayer OpenEXR file and return a dictionary mapping layers to
    either numpy float32 arrays (if ``tonemap=False``) or to 8bit PIL images
    (if ``tonemap=True``).

    :param filename: string filename
    :param tonemap: if ``True``, map to sRGB
    :param thumb_size: if nonzero, resize images to have this as their max dimension
    :param show_progress: if ``True``, print info about loading
    """

    if show_progress:
        print "Reading %s: %s layers..." % (filename, len(LAYER_CHANNELS))

    # Open the input file
    f = OpenEXR.InputFile(filename)
    header = f.header()

    # Compute the size
    dw = header['dataWindow']
    cols, rows = dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1

    multilayer = {}

    # load channels
    FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
    for key, channels in LAYER_CHANNELS.iteritems():
        print "Loading layer %s..." % key
        image = np.empty((rows, cols, 3), dtype=np.float32)
        for (i, c) in enumerate(channels):
            data = f.channel(c, FLOAT)
            image[:, :, i] = np.fromstring(data, dtype=np.float32) \
                .reshape((rows, cols))
        multilayer[key] = image

    #if denoise:
        #for t in ["diff", "gloss", "trans"]:
            #print "Denoising layer %s..." % t
            #multilayer["%s_ind" % t] = denoise_indirect_image(multilayer["%s_ind" % t])

        ## recompute combined image using denoised layer
        #multilayer["combined"] = multilayer["emit"] + multilayer["env"]
        #for t in ["diff", "gloss", "trans"]:
            #multilayer["combined"] += (
                #multilayer["%s_col" % t] * (multilayer["%s_dir" % t] + multilayer["%s_ind" % t])
            #)

    # resize and tonemap
    if tonemap:
        for key, channels in LAYER_CHANNELS.iteritems():
            print "Tonemapping layer %s..." % key
            image = multilayer[key]
            if key == "depth":
                image /= np.max(image[np.isfinite(image)])

            # convert to sRGB PIL
            image = numpy_to_pil(rgb_to_srgb(np.clip(image, 0.0, 1.0)))
            if thumb_size and key != "combined":
                image = ResizeToFit(thumb_size, thumb_size).process(image)
            multilayer[key] = image

    return multilayer


def open_multilayer_exr_layers(inputfile, layers):
    """
    Load a list of images, each corresponding to a layer of an OpenEXR file.

    Note that "layer" does not correspond to a single color channel, like "R",
    but rather, a group of 3 color channels.

    :param inputfile: string filename
    :param layers: list of string layer names
    """
    f = OpenEXR.InputFile(inputfile)
    header = f.header()
    dw = header['dataWindow']
    cols, rows = dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1

    # load channels
    FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
    images = []
    for layer in layers:
        channels = LAYER_CHANNELS[layer]
        image = np.empty((rows, cols, 3), dtype=np.float32)
        for (i, c) in enumerate(channels):
            data = f.channel(c, FLOAT)
            image[:, :, i] = np.fromstring(data, dtype=np.float32) \
                .reshape((rows, cols))
        images.append(image)

    return images


#def denoise_indirect_image(img):
    #denoised = np.empty_like(img)
    #for c in xrange(3):
        #denoised[:, :, c] = median_filter(
            #img[:, :, c],
            #mode='reflect',
            #footprint=[
                #[0, 1, 0],
                #[1, 1, 1],
                #[0, 1, 0],
            #]
        #)
    #return denoised


def update_synthetic_diff_intensity(show_progress=False):
    """ Updates these fields for synthetic images:
        :attr:`intrinsic.models.IntrinsicPoint.synthetic_diff_intensity`
        :attr:`intrinsic.models.IntrinsicPointComparison.synthetic_diff_intensity_ratio`
        :attr:`intrinsic.models.IntrinsicPointComparison.synthetic_diff_cv`
    """

    decomp_iterator = IntrinsicSyntheticDecomposition.objects.all()
    if show_progress:
        decomp_iterator = progress_bar(decomp_iterator)

    for decomp in decomp_iterator:
        diff_col, diff_ind, diff_dir, comb = decomp.open_multilayer_exr_layers(
            ['diff_col', 'diff_ind', 'diff_dir', 'combined'])
        diff = diff_col * (diff_ind + diff_dir)

        points = IntrinsicPoint.objects \
            .filter(photo_id=decomp.photo_id)

        for p in points:
            # diffuse color intensity
            p_diff_col = diff_col[int(p.y * diff_col.shape[0]), int(p.x * diff_col.shape[1]), :]
            p.synthetic_diff_intensity = np.mean(p_diff_col)

            # diffuse energy fraction
            p_diff = diff[int(p.y * diff.shape[0]), int(p.x * diff.shape[1]), :]
            p_comb = comb[int(p.y * comb.shape[0]), int(p.x * comb.shape[1]), :]
            p.synthetic_diff_fraction = np.mean(p_diff) / np.mean(p_comb)

            # coefficient of variation of the local 3x3 block
            px = int(p.x * diff_col.shape[1])
            py = int(p.y * diff_col.shape[0])
            p_diff_col_block = diff_col[
                max(py - 1, 0):min(py + 1, diff_col.shape[0]),
                max(px - 1, 0):min(px + 1, diff_col.shape[1]), :]
            mu_block = np.mean(p_diff_col_block)
            if mu_block > 0:
                p.synthetic_diff_cv = np.std(p_diff_col_block) / mu_block
            else:
                p.synthetic_diff_cv = None

            p.save()

        comparisons = IntrinsicPointComparison.objects \
            .filter(photo_id=decomp.photo_id) \
            .select_related('point1', 'point2')

        for c in comparisons:
            if c.point1.synthetic_diff_intensity >= 1e-3 and c.point2.synthetic_diff_intensity >= 1e-3:
                c.synthetic_diff_intensity_ratio = (
                    c.point1.synthetic_diff_intensity /
                    c.point2.synthetic_diff_intensity
                )
            else:
                c.synthetic_diff_intensity_ratio = None
            c.save()


def compute_optimal_delta(show_progress=False):

    if show_progress:
        print "Loading ground truth..."

    preload = []

    decomp_iterator = IntrinsicSyntheticDecomposition.objects.all()
    if show_progress:
        decomp_iterator = progress_bar(decomp_iterator)

    for decomp in decomp_iterator:
        comparisons = IntrinsicPointComparison.objects \
            .filter(photo_id=decomp.photo_id) \
            .filter(point1__opaque=True, point2__opaque=True, darker__isnull=False) \
            .select_related('point1', 'point2') \

        if not comparisons:
            continue

        diff_col, = decomp.open_multilayer_exr_layers(['diff_col', ])

        preload.append([
            list(comparisons),
            diff_col
        ])

    def objective(thresh):
        if thresh < 0:
            return 1.0

        neq_thresh = 1.0 / (1.0 + thresh)
        eq_thresh = 1.0 + thresh

        errors = []
        for comparisions, diff_col in preload:
            error_sum = 0.0
            weight_sum = 0.0
            for c in comparisons:
                l1, l2 = [
                    np.mean(diff_col[int(p.y * diff_col.shape[0]), int(p.x * diff_col.shape[1]), :])
                    for p in (c.point1, c.point2)
                ]
                if l1 < 1e-3 or l2 < 1e-3:
                    continue

                if c.darker == "1":  # l1 < l2
                    error_sum += 0 if l1 / max(l2, 1e-10) < neq_thresh else c.darker_score
                elif c.darker == "2":  # l2 < l1
                    error_sum += 0 if l2 / max(l1, 1e-10) < neq_thresh else c.darker_score
                elif c.darker == "E":  # l1 - l2
                    ratio = max(l1, l2) / max(min(l1, l2), 1e-10)
                    error_sum += 0 if ratio < eq_thresh else c.darker_score
                else:
                    raise ValueError("Unknown value of darker: %s" % c.darker)

                weight_sum += c.darker_score
            if weight_sum:
                errors.append(error_sum / weight_sum)

        mean_error = np.mean(errors)
        print thresh, mean_error
        return mean_error

    if show_progress:
        print "Optimizing threshold..."

    return float(brute(objective, ranges=[(0.0, 0.5)], disp=show_progress))
