import pywt
import numpy as np


def compute_wavelet_feature_vector(image, wavelet='db6'):
    image_np = np.array(image)
    rgb = [image_np[:, :, i] for i in (0, 1, 2)]

    if isinstance(wavelet, basestring):
        wavelet = pywt.Wavelet(wavelet)

    feature_vector = []
    for c in rgb:
        level = pywt.dwt_max_level(min(c.shape[0], c.shape[1]), wavelet.dec_len)
        levels = pywt.wavedec2(c, wavelet, mode='sym', level=level)
        for coeffs in levels:
            if not isinstance(coeffs, tuple):
                coeffs = (coeffs,)
            for w in coeffs:
                w_flat = w.flatten()
                feature_vector += [float(np.mean(w_flat)), float(np.std(w_flat))]

    return feature_vector
