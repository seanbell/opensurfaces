"""
Utilities for handling 3D vectors, 2D intersections and geometry
"""
import copy
import math
import numpy as np


def matrix_to_column_list(m):
    """ Expand a matrix to a list, column-major order """
    return np.ravel(m, order='F').tolist()


def normalized(v):
    """ Normalize an nd vector """
    norm = np.linalg.norm(v)
    if norm:
        return np.array(v) / norm
    else:
        return v


def normalized_cross(a, b):
    """ 3D cross product """
    return normalized(np.cross(a, b))


def abs_dot(a, b):
    """ Return :math:`|a \dot b|` """
    return abs(np.dot(a, b))


def sphere_to_unit(v):
    """ Convert (theta, phi) to (x, y, z) """
    sin_theta = math.sin(v[0])
    cos_theta = math.cos(v[0])
    return (sin_theta * math.cos(v[1]),
            sin_theta * math.sin(v[1]),
            cos_theta)


def unit_to_sphere(v):
    """ Convert (x, y, z) to (theta, phi) """
    return (math.acos(v[2]), math.atan2(v[1], v[0]))


def rotation_matrix3(axis, theta):
    """ Return the 3x3 rotation matrix around the specified axis (0, 1, or 2) """
    R = np.eye(3)
    c = math.cos(theta)
    s = math.sin(theta)
    a1 = (axis + 1) % 3
    a2 = (axis + 2) % 3
    R[a1, a1] = c
    R[a1, a2] = -s
    R[a2, a1] = s
    R[a2, a2] = c
    return np.matrix(R)


def axis_angle_matrix3(unit, theta):
    """ Return the 3x3 rotation matrix around an arbitrary unit vector """
    x, y, z = unit
    c = math.cos(theta)
    s = math.sin(theta)
    C = 1 - c
    return np.matrix([
        [x * x * C + c, x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, y * y * C + c, y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, z * z * C + c],
    ])


def homo_line(a, b):
    """
    Return the homogenous equation of a line passing through a and b,
    i.e. [ax, ay, 1] cross [bx, by, 1]
    """
    return (a[1] - b[1], b[0] - a[0], a[0] * b[1] - a[1] * b[0])


def vanishing_line(n, focal):
    """ Returns the equation of the vanishing line given a normal """
    return (n[0], n[1], n[2] * focal)


def line_ccw(a, b, p):
    """
    Return which side p is on with respect to line ab.
    """
    return (p[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (p[0] - a[0])


def same_side_product(p, q, a, b):
    """
    Return > 0 if p and q lie on the same side of line ab,
    0 if both on the line, and < 0 if on opposite sides of the line.
    """
    return line_ccw(a, b, p) * line_ccw(a, b, q)


def orthogonalize_matrix(m):
    """ Returns the closest orthogonal matrix to m (closest as measured by
    Frobenius norm) """
    U, __, VT = np.linalg.svd(np.matrix(m))
    return np.dot(U, VT)


def triangle_segment_intersects(t0, t1, t2, p0, p1):
    """ Return whether line p0,p1 intersects triangle t0,t1,t2.  Containment
    counts as intersection.  """
    # if all 3 vertices are on the same side of the line, there is no
    # intersection
    s = line_ccw(p0, p1, t0)
    if s == line_ccw(p0, p1, t1) and s == line_ccw(p0, p1, t2):
        return False

    # if the line is outside one of the triangle half-planes, there is no
    # intersection
    for (a, b, c) in ((t0, t1, t2), (t1, t2, t0), (t2, t0, t1)):
        s = line_ccw(a, b, c)  # find side of triangle
        if s != line_ccw(a, b, p0) and s != line_ccw(a, b, p1):
            return False

    # intersection
    return True


def triangle_point_intersects(a, b, c, s):
    """ Return whether point s intersects triangle a,b,c.  """
    return (
        line_ccw(a, b, c) == line_ccw(a, b, s) and
        line_ccw(b, c, a) == line_ccw(b, c, s) and
        line_ccw(c, a, b) == line_ccw(c, a, s)
    )


def segment_segment_intersects(a, b, c, d):
    """ Return whether segment ab intersects cd where a, b, c, d are point
    tuples.  """
    return (line_ccw(a, c, d) != line_ccw(b, c, d) and
            line_ccw(a, b, c) != line_ccw(a, b, d))


def segment_point_distance_sq(x1, y1, x2, y2, px, py):
    """ Return the distance from segment (x1, y1, x2, y2) to point (px, py) """
    pd2 = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)
    if pd2 == 0:
        # Points are coincident.
        x = x1
        y = y2
    else:
        # parameter of closest point on the line
        u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / pd2
        if u < 0:  # off the end
            x = x1
            y = y1
        elif u > 1.0:  # off the end
            x = x2
            y = y2
        else:  # interpolate
            x = x1 + u * (x2 - x1)
            y = y1 + u * (y2 - y1)
    return (x - px) * (x - px) + (y - py) * (y - py)


def bbox_point_intersects(bbox, a):
    return (a[0] >= bbox[0] and a[0] <= bbox[2] and
            a[1] >= bbox[1] and a[1] <= bbox[3])


def bbox_segment_intersects(bbox, a, b):
    """
    Return true if the bbox contains or partially intersects segment a.
    """
    # check whether the line is completely left/right/above/below the bbox
    if ((a[0] < bbox[0] and b[0] < bbox[0]) or
        (a[0] > bbox[2] and b[0] > bbox[2]) or
        (a[1] < bbox[1] and b[1] < bbox[1]) or
            (a[1] > bbox[3] and b[1] > bbox[2])):
        return False

    # Check whether any of the four bbox points are on different sides of the
    # line.
    h = homo_line(a, b)
    s = [
        h[0] * p[0] + h[1] * p[1] + h[2] > 0 for p in
        [(bbox[0], bbox[1]), (bbox[0], bbox[3]),
         (bbox[2], bbox[1]), (bbox[2], bbox[3])]
    ]
    return (s[0] != s[1] or s[0] != s[2] or s[0] != s[3])


def triangles_segments_intersections_only(
        vertices, segments, triangles, query_segments):
    """
    Return the indices of the query segments that intersect any of the triangles,
    but none of the segments.
    vertices are a list of point tuples, segments are lists of tuples of indices into vertices,
    and triangles are lists of tuples of indices into vertices.
    query_segments are a list of point tuples [((x1, y1), (x2, y2)), ...].
    """

    from shapes.utils import bbox_vertices
    bbox = bbox_vertices(vertices)

    ret = []
    for (idx, (a, b)) in enumerate(query_segments):
        if not bbox_segment_intersects(bbox, a, b):
            continue

        # intersect with each segment
        for (s0, s1) in segments:
            if segment_segment_intersects(
                    vertices[s0], vertices[s1], a, b):
                continue

        # intersect with each triangle
        for (t0, t1, t2) in triangles:
            if triangle_segment_intersects(
                    vertices[t0], vertices[t1], vertices[t2], a, b):
                ret.append(idx)

    return ret


def complex_polygon_centroid(vertices, triangles):
    cw, cx, cy = 0.0, 0.0, 0.0
    for t in triangles:
        a, b, c = [vertices[i] for i in t]
        w = triangle_area(a, b, c)
        cx += (a[0] + b[0] + c[0]) * w / 3
        cy += (a[1] + b[1] + c[1]) * w / 3
        cw += w
    return (cx / cw, cy / cw)


def triangle_area(a, b, c):
    """ Return the area of the triangle defined by ``[a, b, c]``, where each
    vertex contains floats ``[x, y]`` """

    return 0.5 * abs(
        a[0] * (b[1] - c[1]) +
        b[0] * (c[1] - a[1]) +
        c[0] * (a[1] - b[1])
    )


def construct_uvn_frame(n, u, b=None, flip_to_match_image=True):
    """ Returns an orthonormal 3x3 frame from a normal and one in-plane vector """

    n = normalized(n)
    u = normalized(np.array(u) - np.dot(n, u) * n)
    v = normalized_cross(n, u)

    # flip to match image orientation
    if flip_to_match_image:
        if abs(u[1]) > abs(v[1]):
            u, v = v, u
        if u[0] < 0:
            u = np.negative(u)
        if v[1] < 0:
            v = np.negative(v)
        if b is None:
            if n[2] < 0:
                n = np.negative(n)
        else:
            if np.dot(n, b) > 0:
                n = np.negative(n)

    # return uvn matrix, column major
    return np.matrix([
        [u[0], v[0], n[0]],
        [u[1], v[1], n[1]],
        [u[2], v[2], n[2]],
    ])


def construct_all_uvn_frames(vectors, flip_to_match_image=True):
    ret = []
    vectors = complete_vector_triplets(vectors)
    for n in vectors:
        u = most_orthogonal_vector(n, vectors)
        if u is not None:
            ret.append(construct_uvn_frame(n, u))
    return ret


def most_parallel_vector(v, vectors, tolerance_dot=0.0):
    """ Returns the most parallel vector to v, from the set w.  The vector
    must also be at least as parallel as the tolerance.  If nothing is that
    parallel, None is returned.  All vectors are assumed to be unit length.
    """

    best_dot = tolerance_dot
    best_w = None
    for w in vectors:
        d = abs_dot(v, w)
        if d > best_dot:
            best_dot = d
            best_w = w
    return best_w


def most_orthogonal_vector(v, vectors, tolerance_dot=1.0):
    """ Returns the most orthogonal vector to v, from the set w.  The vector
    must also be at least as orthogonal as the tolerance.  If nothing is that
    orthogonal, None is returned.  All vectors are assumed to be unit length.
    """

    best_dot = tolerance_dot
    best_w = None
    for w in vectors:
        d = abs_dot(v, w)
        if d < best_dot:
            best_dot = d
            best_w = w
    return best_w


def complete_vector_triplets(vectors, tolerance_dot=0.90630778703):
    """ Completes any missing orthogonal triplets in a set of unit vectors.
    Returns the completed set of vectors. """

    new_vectors = copy.copy(vectors)
    if len(vectors) >= 2:
        for i1, v1 in enumerate(vectors):
            for v2 in vectors[:i1]:
                v = normalized_cross(v1, v2)
                if all(abs_dot(v, v3) < tolerance_dot for v3 in new_vectors):
                    new_vectors.append(v)
    return new_vectors


def simplify_polyline_epsilon(points, epsilon):
    """ Simplify a polyline based on the Ramer-Douglas-Peucker Algorithm
    (http://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm)
    Implementation adapted from:
    http://stackoverflow.com/questions/2573997/reduce-number-of-points-in-line
    """
    raise NotImplementedError("TODO: test this code")

    if len(points) < 3:
        return points

    begin, end = points[0], points[-1]
    dist_sq = [segment_point_distance_sq(
        begin[0], begin[1], end[0], end[1], p[0], p[1])
        for p in points[1:-1]]

    maxdist = max(dist_sq)
    if maxdist < epsilon ** 2:
        return [begin, end]

    pos = dist_sq.index(maxdist)
    return (simplify_polyline_epsilon(points[:pos + 2], epsilon) +
            simplify_polyline_epsilon(points[pos + 1:], epsilon)[1:])


def bbox_svg_transform(box):
    """ SVG transform to zoom into bbox """
    return u"scale(%s,%s) translate(%s,%s)" % (
        1.0 / (box[2] - box[0]),
        1.0 / (box[3] - box[1]),
        -box[0], -box[1],
    )
