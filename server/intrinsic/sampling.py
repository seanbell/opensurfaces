from decimal import Decimal
import numpy as np
from numpy.linalg import norm
from scipy.spatial import Delaunay
from scipy.stats import variation
from skimage.filter import canny
from skimage.color import rgb2lab

from common.geom import segment_segment_intersects
from common.sampling import sample_poisson_uniform
from photos.utils import pil_to_numpy
from intrinsic.models import IntrinsicPoint, IntrinsicPointComparison


def sample_photo_intrinsic_points(
        photo, width=2048, min_separation=Decimal('0.07'),
        edge_window=4, side_thresh=40, avoid_existing_points=True,
        **kwargs):
    """ Populate a photograph with evenly spaced samples that avoid image edges
    (canny), high gradient (gaussian) regions, and very dark regions """

    # detect edges and compute gradients
    image = pil_to_numpy(photo.open_image(width=width))
    image_lab = rgb2lab(image)
    rows, cols, _ = image.shape

    #image_sobel = sobel(rgb2gray(image))
    image_canny = (
        canny(image[:, :, 0], sigma=2.0) |
        canny(image[:, :, 1], sigma=2.0) |
        canny(image[:, :, 2], sigma=2.0)
    )

    # avoid existing points
    if avoid_existing_points:
        existing_points = [
            (x * cols, y * rows) for (x, y) in IntrinsicPoint.objects
            .filter(photo=photo, min_separation=min_separation)
            .values_list('x', 'y')
        ]
    else:
        existing_points = []

    # min radius
    r = max(1, int(np.sqrt(cols ** 2 + rows ** 2) * float(min_separation)))
    r_sq = r ** 2

    # filter: not near the edge, on an image edge, and not on a high gradient
    def point_filter(p):
        # not near any existing points
        for q in existing_points:
            if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < r_sq:
                return False

        c, r = int(p[0]), int(p[1])
        # cannot be near the edge of the image
        if (c < side_thresh or r < side_thresh or
                cols - c < side_thresh or rows - r < side_thresh):
            return False
        # cannot be super bright or dark
        if not (0.02 < np.mean(image[r, c, :]) < 0.98):
            return False
        # cannot be on an edge
        r0, r1 = max(r - edge_window, 0), min(r + edge_window + 1, rows)
        c0, c1 = max(c - edge_window, 0), min(c + edge_window + 1, cols)
        if np.any(image_canny[r0:r1, c0:c1]):
            return False
        # chromaticity coefficient of variation cannot be too high
        # (cv = std / mean)
        chroma_cv = 0.5 * (
            variation(image_lab[r0:r1, c0:c1, 1], axis=None) +
            variation(image_lab[r0:r1, c0:c1, 2], axis=None)
        )
        return chroma_cv < 0.50

    # poisson disk sampling
    samples = sample_poisson_uniform(
        width=cols, height=rows, r=r, k=30, n_seeds=10000,
        point_filter=point_filter)

    # store in database
    intrinsic_points = []
    for p in samples:
        x = float(p[0]) / cols
        y = float(p[1]) / rows
        sRGB = '%02x%02x%02x' % photo.get_pixel(x, y, width='300')
        intrinsic_points.append(IntrinsicPoint(
            photo=photo, x=x, y=y, sRGB=sRGB,
            min_separation=min_separation,
        ))
    if intrinsic_points:
        IntrinsicPoint.objects.bulk_create(intrinsic_points)


def sample_photo_intrinsic_comparisons(
        photo, min_separation=Decimal('0.07'), chromaticity_thresh=0.125, **kwargs):
    """ Pairwise add all samples that have similar chromaticity and low
    intensity """

    # resulting objects
    edges = {}

    # prefetch all points
    points = list(photo.intrinsic_points.filter(min_separation=min_separation))
    id_to_points = {p.id: p for p in points}

    # triangulate
    if len(points) < 3:
        return
    elif len(points) == 3:
        tris = np.array([[0, 1, 2]])
    else:
        tris = Delaunay([[p.x, p.y] for p in points]).simplices

    # compare function for points
    def cmp_points(p1, p2):
        if p1.x == p2.x:
            return cmp(p1.y, p2.y)
        return cmp(p1.x, p2.x)

    # whether we keep edges or not
    def keep_edge(p1, p2):
        if (p1.id, p2.id) in edges:
            return False
        elif chromaticity_thresh and (norm(p1.get_chroma() - p2.get_chroma()) > chromaticity_thresh):
            return False
        return True

    for tri_idx in xrange(tris.shape[0]):
        tri_pts = [points[idx] for idx in tris[tri_idx, :]]
        p1, p2, p3 = sorted(tri_pts, cmp=cmp_points)

        # each edge in the triangle
        for (point1, point2) in [(p1, p2), (p2, p3), (p1, p3)]:
            if keep_edge(point1, point2):
                edges[(point1.id, point2.id)] = IntrinsicPointComparison(
                    photo=photo, point1=point1, point2=point2,
                )

    if chromaticity_thresh:

        # sort edges by distance: consider shortest edges first
        possible_edges = []
        for i1, p1 in enumerate(points):
            for p2 in points[0:i1]:
                p1, p2 = sorted([p1, p2], cmp=cmp_points)
                if keep_edge(p1, p2):
                    possible_edges.append((p1, p2))
        possible_edges.sort(key=lambda (p1, p2): (
            ((p1.x - p2.x) * photo.aspect_ratio) ** 2 + (p1.y - p2.y) ** 2)
        )

        def intersects_existing(p1, p2):
            for e in edges:
                q1, q2 = [id_to_points[id] for id in e]
                if p1 == q1 or p2 == q2 or p1 == q2 or p2 == q1:
                    continue
                if (segment_segment_intersects(
                        (p1.x, p1.y), (p2.x, p2.y),
                        (q1.x, q1.y), (q2.x, q2.y))):
                    return True
            return False

        # use each edge if it intersects nothing
        for p1, p2 in possible_edges:
            if not intersects_existing(p1, p2):
                edges[(p1.id, p2.id)] = IntrinsicPointComparison(
                    photo=photo, point1=p1, point2=p2,
                    point1_image_darker=(p1.get_lab()[0] < p2.get_lab()[0])
                )

    # add to database
    if edges:
        for comparison in edges.values():
            if IntrinsicPointComparison.objects.filter(
                    point1=comparison.point1, point2=comparison.point2).exists():
                print 'Duplicate edge: %s %s!' % (point1.id, point2.id)
            else:
                comparison.save()
