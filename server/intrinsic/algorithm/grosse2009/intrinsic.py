import itertools
import numpy as np
import os
import png
import sys

import poisson


############################### Data ###########################################

def load_png(fname):
    reader = png.Reader(fname)
    w, h, pngdata, params = reader.read()
    image = np.vstack(itertools.imap(np.uint16, pngdata))
    if image.size == 3*w*h:
        image = np.reshape(image, (h, w, 3))
    return image.astype(float) / 255.

def load_object_helper(tag, condition):
    """Load an image of a given object as a NumPy array. The values condition may take are:

            'mask', 'original', 'diffuse', 'shading', 'reflectance', 'specular'

    'shading' returns a grayscale image, and all the other options return color images."""
    assert condition in ['mask', 'original', 'diffuse', 'shading', 'reflectance', 'specular']

    obj_dir = os.path.join('data', tag)

    if condition == 'mask':
        filename = os.path.join(obj_dir, 'mask.png')
        mask = load_png(filename)
        return (mask > 0)
    if condition == 'original':
        filename = os.path.join(obj_dir, 'original.png')
        return load_png(filename)
    if condition == 'diffuse':
        filename = os.path.join(obj_dir, 'diffuse.png')
        return load_png(filename)
    if condition == 'shading':
        filename = os.path.join(obj_dir, 'shading.png')
        return load_png(filename)
    if condition == 'reflectance':
        filename = os.path.join(obj_dir, 'reflectance.png')
        return load_png(filename)
    if condition == 'specular':
        filename = os.path.join(obj_dir, 'specular.png')
        return load_png(filename)

# cache for efficiency because PyPNG is pure Python
cache = {}
def load_object(tag, condition):
    if (tag, condition) not in cache:
        cache[tag, condition] = load_object_helper(tag, condition)
    return cache[tag, condition]

def load_multiple(tag):
    """Load the images of a given object for all lighting conditions. Returns an
    m x n x 3 x 10 NumPy array, where the third dimension is the color channel and
    the fourth dimension is the image number."""
    obj_dir = os.path.join('data', tag)
    filename = os.path.join(obj_dir, 'light01.png')
    img0 = load_png(filename)
    result = np.zeros(img0.shape + (10,))


    for i in range(10):
        filename = os.path.join(obj_dir, 'light%02d.png' % (i+1))
        result[:,:,:,i] = load_png(filename)

    return result



############################# Error metric #####################################

def ssq_error(correct, estimate, mask):
    """Compute the sum-squared-error for an image, where the estimate is
    multiplied by a scalar which minimizes the error. Sums over all pixels
    where mask is True. If the inputs are color, each color channel can be
    rescaled independently."""
    assert correct.ndim == 2
    if np.sum(estimate**2 * mask) > 1e-5:
        alpha = np.sum(correct * estimate * mask) / np.sum(estimate**2 * mask)
    else:
        alpha = 0.
    return np.sum(mask * (correct - alpha*estimate) ** 2)

def local_error(correct, estimate, mask, window_size, window_shift):
    """Returns the sum of the local sum-squared-errors, where the estimate may
    be rescaled within each local region to minimize the error. The windows are
    window_size x window_size, and they are spaced by window_shift."""
    M, N = correct.shape[:2]
    ssq = total = 0.
    for i in range(0, M - window_size + 1, window_shift):
        for j in range(0, N - window_size + 1, window_shift):
            correct_curr = correct[i:i+window_size, j:j+window_size]
            estimate_curr = estimate[i:i+window_size, j:j+window_size]
            mask_curr = mask[i:i+window_size, j:j+window_size]
            ssq += ssq_error(correct_curr, estimate_curr, mask_curr)
        total += np.sum(mask_curr * correct_curr**2)
    assert -np.isnan(ssq/total)

    return ssq / total

def score_image(true_shading, true_refl, estimate_shading, estimate_refl, mask, window_size=20):
    return 0.5 * local_error(true_shading, estimate_shading, mask, window_size, window_size//2) + \
           0.5 * local_error(true_refl, estimate_refl, mask, window_size, window_size//2)




################################## Algorithms ##################################


def retinex(image, mask, threshold, L1=False):
    image = np.clip(image, 3., np.infty)
    log_image = np.where(mask, np.log(image), 0.)
    i_y, i_x = poisson.get_gradients(log_image)

    r_y = np.where(np.abs(i_y) > threshold, i_y, 0.)
    r_x = np.where(np.abs(i_x) > threshold, i_x, 0.)

    if L1:
        log_refl = poisson.solve_L1(r_y, r_x, mask)
    else:
        log_refl = poisson.solve(r_y, r_x, mask)
    refl = mask * np.exp(log_refl)

    return np.where(mask, image / refl, 0.), refl

def project_gray(i_y):
    i_y_mean = np.mean(i_y, axis=2)
    result = np.zeros(i_y.shape)
    for i in range(3):
        result[:,:,i] = i_y_mean
    return result

def project_chromaticity(i_y):
    return i_y - project_gray(i_y)

def color_retinex(image, mask, threshold_gray, threshold_color, L1=False):
    image = np.clip(image, 3., np.infty)

    log_image = np.log(image)
    i_y_orig, i_x_orig = poisson.get_gradients(log_image)
    i_y_gray, i_y_color = project_gray(i_y_orig), project_chromaticity(i_y_orig)
    i_x_gray, i_x_color = project_gray(i_x_orig), project_chromaticity(i_x_orig)

    image_grayscale = np.mean(image, axis=2)
    image_grayscale = np.clip(image_grayscale, 3., np.infty)
    log_image_grayscale = np.log(image_grayscale)
    i_y, i_x = poisson.get_gradients(log_image_grayscale)

    norm = np.sqrt(np.sum(i_y_color**2, axis=2))
    i_y_match = (norm > threshold_color) + (np.abs(i_y_gray[:,:,0]) > threshold_gray)

    norm = np.sqrt(np.sum(i_x_color**2, axis=2))
    i_x_match = (norm > threshold_color) + (np.abs(i_x_gray[:,:,0]) > threshold_gray)

    r_y = np.where(i_y_match, i_y, 0.)
    r_x = np.where(i_x_match, i_x, 0.)

    if L1:
        log_refl = poisson.solve_L1(r_y, r_x, mask)
    else:
        log_refl = poisson.solve(r_y, r_x, mask)
    refl =  np.exp(log_refl)

    return image_grayscale / refl, refl

def weiss(image, multi_images, mask, L1=False):
    multi_images = np.clip(multi_images, 3., np.infty)
    log_multi_images = np.log(multi_images)

    i_y_all, i_x_all = poisson.get_gradients(log_multi_images)
    r_y = np.median(i_y_all, axis=2)
    r_x = np.median(i_x_all, axis=2)
    if L1:
        log_refl = poisson.solve_L1(r_y, r_x, mask)
    else:
        log_refl = poisson.solve(r_y, r_x, mask)
    refl = np.where(mask, np.exp(log_refl), 0.)
    shading = np.where(mask, image / refl, 0.)

    return shading, refl

def weiss_retinex(image, multi_images, mask, threshold, L1=False):
    multi_images = np.clip(multi_images, 3., np.infty)
    log_multi_images = np.log(multi_images)

    i_y_all, i_x_all = poisson.get_gradients(log_multi_images)
    r_y = np.median(i_y_all, axis=2)
    r_x = np.median(i_x_all, axis=2)

    r_y *= (np.abs(r_y) > threshold)
    r_x *= (np.abs(r_x) > threshold)
    if L1:
        log_refl = poisson.solve_L1(r_y, r_x, mask)
    else:
        log_refl = poisson.solve(r_y, r_x, mask)
    refl = np.where(mask, np.exp(log_refl), 0.)
    shading = np.where(mask, image / refl, 0.)

    return shading, refl





#################### Wrapper classes for experiments ###########################


class BaselineEstimator:
    """Assume every image is entirely shading or entirely reflectance."""
    def __init__(self, mode, L1=False):
        assert mode in ['refl', 'shading']
        self.mode = mode

    def estimate_shading_refl(self, image, mask, L1=False):
        if self.mode == 'refl':
            refl = image
            shading = 1. * mask
        else:
            refl = 1. * mask
            shading = image
            return shading, refl

    @staticmethod
    def get_input(tag):
        image = load_object(tag, 'diffuse')
        image = np.mean(image, axis=2)
        mask = load_object(tag, 'mask')
        return image, mask

    @staticmethod
    def param_choices():
        return [{'mode': m} for m in ['shading', 'refl']]


class GrayscaleRetinexEstimator:
    def __init__(self, threshold):
        self.threshold = threshold

    def estimate_shading_refl(self, image, mask, L1=False):
        return retinex(image, mask, self.threshold, L1)

    @staticmethod
    def get_input(tag):
        image = load_object(tag, 'diffuse')
        image = np.mean(image, axis=2)
        mask = load_object(tag, 'mask')
        return image, mask

    @staticmethod
    def param_choices():
        return [{'threshold': t} for t in np.logspace(-3., 1., 15)]


class ColorRetinexEstimator:
    def __init__(self, threshold_gray, threshold_color, L1=False):
        self.threshold_gray = threshold_gray
        self.threshold_color = threshold_color

    def estimate_shading_refl(self, image, mask, L1=False):
        return color_retinex(image, mask, self.threshold_gray, self.threshold_color, L1)

    @staticmethod
    def get_input(tag):
        image = load_object(tag, 'diffuse')
        mask = load_object(tag, 'mask')
        return image, mask

    @staticmethod
    def param_choices():
        return [{'threshold_gray': tg, 'threshold_color': tc}
                for tg in np.logspace(-1.5, 0., 5)
                for tc in np.logspace(-1.5, 0., 5)]


class WeissEstimator:
    def estimate_shading_refl(self, image, multi_images, mask, L1=False):
        return weiss(image, multi_images, mask, L1)

    @staticmethod
    def get_input(tag):
        image = load_object(tag, 'diffuse')
        image = np.mean(image, axis=2)
        mask = load_object(tag, 'mask')
        multi_images = load_multiple(tag)
        multi_images = np.mean(multi_images, axis=2)
        return image, multi_images, mask

    @staticmethod
    def param_choices():
        return [{}]


class WeissRetinexEstimator:
    def __init__(self, threshold=0.1, L1=False):
        self.threshold = threshold

    def estimate_shading_refl(self, image, multi_images, mask, L1=False):
        return weiss_retinex(image, multi_images, mask, self.threshold, L1)

    @staticmethod
    def get_input(tag):
        image = load_object(tag, 'diffuse')
        image = np.mean(image, axis=2)
        mask = load_object(tag, 'mask')
        multi_images = load_multiple(tag)
        multi_images = np.mean(multi_images, axis=2)
        return image, multi_images, mask

    @staticmethod
    def param_choices():
        return [{'threshold': t} for t in np.logspace(-3., 1., 15)]

