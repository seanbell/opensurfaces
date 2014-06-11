import math
import json

import numpy as np
from numpy import linalg

from PIL import Image
from imagekit.utils import open_image

from shapes.utils import parse_vertices, \
    bbox_vertices, mask_complex_polygon


def projection_function(homography):
    """
    Returns a function that applies a homography (3x3 matrix) to 2D tuples
    """
    H = np.copy(homography)

    def project(uv):
        xy = H * np.matrix([[uv[0]], [uv[1]], [1]])
        return (float(xy[0] / xy[2]), float(xy[1] / xy[2]))
    return project


def rectify_shape_from_uvnb(shape, rectified_normal, max_dim=None):
    """
    Returns the rectified PIL image

    shape: MaterialShape instance
    rectified_normal: ShapeRectifiedNormalLabel instance

    pq: original pixel coordinates with y down
    xy: centered pixel coordinates with y up
    uv: in-plane coordinates (arbitrary) with y up
    st: rescaled and shifted plane coordinates (fits inside [0,1]x[0,1] but
        with correct aspect ratio) with y down
    ij: scaled final pixel plane coordinates with y down
    """

    # helper function that applies a homography
    def transform(H, points):
        proj = projection_function(H)
        return [proj(p) for p in points]

    # grab original photo info
    w = shape.photo.image_orig.width
    h = shape.photo.image_orig.height
    focal_pixels = 0.5 * max(w, h) / math.tan(math.radians(
        0.5 * shape.photo.fov))

    # uvnb: [u v n b] matrix arranged in column-major order
    uvnb = [float(f) for f in json.loads(rectified_normal.uvnb)]

    # mapping from plane coords to image plane
    M_uv_to_xy = np.matrix([
        [focal_pixels, 0, 0],
        [0, focal_pixels, 0],
        [0, 0, -1]
    ]) * np.matrix([
        [uvnb[0], uvnb[4], uvnb[12]],
        [uvnb[1], uvnb[5], uvnb[13]],
        [uvnb[2], uvnb[6], uvnb[14]]
    ])
    M_xy_to_uv = linalg.inv(M_uv_to_xy)

    M_pq_to_xy = np.matrix([
        [1, 0, -0.5 * w],
        [0, -1, 0.5 * h],
        [0, 0, 1],
    ])

    verts_pq = [(v[0] * w, v[1] * h) for v in parse_vertices(shape.vertices)]
    #print 'verts_pq:', verts_pq

    # estimate rough resolution from original bbox
    if not max_dim:
        min_p, min_q, max_p, max_q = bbox_vertices(verts_pq)
        max_dim = max(max_p - min_p, max_q - min_q)
    #print 'max_dim:', max_dim

    # transform
    verts_xy = transform(M_pq_to_xy, verts_pq)
    #print 'verts_xy:', verts_pq
    verts_uv = transform(M_xy_to_uv, verts_xy)
    #print 'verts_uv:', verts_uv

    # compute bbox in uv plane
    min_u, min_v, max_u, max_v = bbox_vertices(verts_uv)
    max_uv_range = float(max(max_u - min_u, max_v - min_v))
    #print 'max_uv_range:', max_uv_range

    # scale so that st fits inside [0, 1] x [0, 1]
    # (but with the correct aspect ratio)
    M_uv_to_st = np.matrix([
        [1, 0, -min_u],
        [0, -1, max_v],
        [0, 0, max_uv_range]
    ])

    verts_st = transform(M_uv_to_st, verts_uv)
    #print 'verts_st:', verts_st

    M_st_to_ij = np.matrix([
        [max_dim, 0, 0],
        [0, max_dim, 0],
        [0, 0, 1]
    ])

    verts_ij = transform(M_st_to_ij, verts_st)
    #print 'verts_ij:', verts_ij

    # find final bbox
    min_i, min_j, max_i, max_j = bbox_vertices(verts_ij)
    size = (int(math.ceil(max_i)), int(math.ceil(max_j)))
    #print 'i: %s to %s, j: %s to %s' % (min_i, max_i, min_j, max_j)
    #print 'size:', size

    # homography for final pixels to original pixels (ij --> pq)
    M_pq_to_ij = M_st_to_ij * M_uv_to_st * M_xy_to_uv * M_pq_to_xy
    M_ij_to_pq = linalg.inv(M_pq_to_ij)
    M_ij_to_pq /= M_ij_to_pq[2, 2]  # NORMALIZE!
    data = M_ij_to_pq.ravel().tolist()[0]
    image = open_image(shape.photo.image_orig)
    rectified = image.transform(size=size, method=Image.PERSPECTIVE,
                                data=data, resample=Image.BICUBIC)

    # crop to polygon
    verts_ij_normalized = [(v[0] / size[0], v[1] / size[1]) for v in verts_ij]
    image_crop, image_bbox = mask_complex_polygon(
        rectified, verts_ij_normalized, shape.triangles)
    return image_crop
