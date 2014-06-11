"""
Utilities for handling shape perspective, vanishing points, and perspective
"""
import json
import copy

from normals.models import ShapeRectifiedNormalLabel
from common.geom import abs_dot, normalized, normalized_cross, \
    complete_vector_triplets, construct_uvn_frame, most_orthogonal_vector


def vanishing_point_to_vector(photo, v):
    """ Return the 3D vector corresponding to a vanishing point (specified in
    normalized coordinates) """

    return normalized((
        (v[0] - 0.5) * photo.aspect_ratio,
        0.5 - v[1],  # flip y coordinate
        -photo.focal_y
    ))


def estimate_uvnb_from_vanishing_points(shape, try_fully_automatic=False):
    """ Return (uvnb, num_vanishing_points) """

    print 'estimate_uvnb for shape_id: %s' % shape.id

    # local import to avoid cyclic dependencies
    from shapes.utils import parse_vertices, parse_triangles, \
        parse_segments, bbox_vertices

    # load photo
    photo = shape.photo

    if not photo.vanishing_lines or not photo.vanishing_points:
        raise ValueError("Vanishing points not computed")

    if not photo.focal_y:
        raise ValueError("Photo does not have focal_y")

    vlines = json.loads(photo.vanishing_lines)
    vpoints = json.loads(photo.vanishing_points)
    vvectors = copy.copy(photo.vanishing_vectors())

    if len(vlines) != len(vpoints):
        raise ValueError("Invalid vanishing points data structure")

    # add any missing vanishing points
    vvectors = complete_vector_triplets(vvectors, tolerance_dot=0.75)

    # find vanishing lines inside shape
    vertices = parse_vertices(shape.vertices)
    segments = parse_segments(shape.triangles)
    triangles = parse_triangles(shape.triangles)

    # intersect shapes with segments
    counts = []
    for idx in xrange(len(vlines)):
        # re-pack for geom routines
        query_segments = [((l[0], l[1]), (l[2], l[3])) for l in vlines[idx]]

        from common.geom import triangles_segments_intersections_only
        n = len(triangles_segments_intersections_only(
            vertices, segments, triangles, query_segments))
        if n >= 5:
            counts.append((n, idx))
    counts.sort(key=lambda x: x[0], reverse=True)

    # function to judge normals: its vanishing line can't intersect the shape.
    def auto_normal_acceptable(n):
        sign = None
        for (x, y) in vertices:
            # vanishing line
            line = (n[0], n[1], n[2] * photo.focal_y)
            # signed distance
            d = (
                (x - 0.5) * photo.aspect_ratio * line[0] +
                (0.5 - y) * line[1] +  # flip y
                line[2]
            )
            if abs(d) < 0.05:
                return False
            elif sign is None:
                sign = (d > 0)
            else:
                if sign != (d > 0):
                    return False
        return True

    # find coordinate frame
    best_n = None
    best_u = None
    method = None
    num_vanishing_lines = 0

    # make sure shape has label
    if not shape.label_pos_x or not shape.label_pos_y:
        from shapes.utils import update_shape_label_pos
        update_shape_label_pos(shape)

    # place label in 3D
    b_z = -(photo.focal_y / photo.aspect_ratio) / 0.1
    b = [
        (shape.label_pos_x - 0.5) * photo.aspect_ratio * (-b_z) / photo.focal_y,
        (0.5 - shape.label_pos_y) * (-b_z) / photo.focal_y,
        b_z
    ]

    # estimate closest human normal
    human_labels = list(ShapeRectifiedNormalLabel.objects.filter(
        shape=shape, automatic=False, correct_score__isnull=False,
    ).order_by('-correct_score'))
    human_labels += list(ShapeRectifiedNormalLabel.objects.filter(
        shape=shape, automatic=False, correct_score__isnull=True))
    if human_labels:
        for label in human_labels:
            human_u = label.u()
            human_n = label.n()
            b = list(label.uvnb_numpy()[0:3, 3].flat)

            # find best normal
            best_n_dot = 0.9
            best_n = None
            for n in vvectors:
                d = abs_dot(human_n, n)
                if d > best_n_dot:
                    best_n_dot = d
                    best_n = n
                    method = 'S'

            # if there is a match find u and quit
            if best_n is not None:
                # find best u
                best_u_dot = 0
                best_u = None
                for u in vvectors:
                    if abs_dot(u, best_n) < 0.1:
                        d = abs_dot(human_u, u)
                        if d > best_u_dot:
                            best_u_dot = d
                            best_u = u
                break

    # try using object label
    if best_n is None and shape.name:
        if shape.name.name.lower() in ('floor', 'carpet/rug', 'ceiling'):
            best_y = 0.9
            for v in vvectors[0:3]:
                if abs(v[1]) > best_y:
                    best_y = abs(v[1])
                    best_n = v
                    method = 'O'

    # try fully automatic method if human normals are not good enough
    if (try_fully_automatic and best_n is None and len(vpoints) >= 3 and len(counts) >= 2 and
            (shape.substance is None or shape.substance.name != 'Painted')):

        # choose two dominant vanishing points
        best_u = vvectors[counts[0][1]]
        best_v = vvectors[counts[1][1]]

        # don't try and auto-rectify frontal surfaces
        if auto_normal_acceptable(normalized_cross(best_u, best_v)):
            num_vanishing_lines = counts[0][0] + counts[1][0]
            uv_dot = abs_dot(best_u, best_v)
            print 'u dot v = %s' % uv_dot
        else:
            best_u, best_v = None, None
            uv_dot = None

        # make sure these vectors are accurate
        if not uv_dot or uv_dot > 0.05:
            # try and find two other orthogonal vanishing points
            best_dot = 0.05
            best_u = None
            best_v = None
            for c1, i1 in counts:
                for c2, i2 in counts[:i1]:
                    d = abs_dot(vvectors[i1], vvectors[i2])
                    if d < best_dot:
                        # don't try and auto-rectify frontal surfaces
                        if auto_normal_acceptable(normalized_cross(
                                vvectors[i1], vvectors[i2])):
                            best_dot = d
                            if c1 > c2:
                                best_u = vvectors[i1]
                                best_v = vvectors[i2]
                            else:
                                best_u = vvectors[i2]
                                best_v = vvectors[i1]
                            num_vanishing_lines = c1 + c2

        if best_u is not None and best_v is not None:
            best_n = normalized_cross(best_u, best_v)
            method = 'A'

            # give up for some classes of objects
            if shape.name:
                name = shape.name.name.lower()
                if ((abs(best_n[1]) > 0.5 and name in (
                        'wall', 'door', 'window')) or
                    (abs(best_n[1]) < 0.5 and name in (
                        'floor', 'ceiling', 'table',
                        'worktop/countertop', 'carpet/rug'))):
                    method = best_u = best_v = best_n = None
                    num_vanishing_lines = 0

    # for walls that touch the edge of the photo, try using bbox center as a
    # vanishing point (i.e. assume top/bottom shapes are horizontal, side
    # shapes are vertical)
    if (try_fully_automatic and best_n is None and shape.name and
            (shape.substance is None or shape.substance.name != 'Painted')):
        if shape.name.name.lower() == 'wall':
            bbox = bbox_vertices(parse_vertices(shape.vertices))
            if ((bbox[0] < 0.05 and bbox[2] < 0.50) or
                    (bbox[0] > 0.50 and bbox[2] > 0.95)):

                bbox_n = photo.vanishing_point_to_vector((
                    0.5 + 10 * (bbox[0] + bbox[2] - 1), 0.5
                ))

                # find normal that best matches this fake bbox normal
                best_n_dot = 0.9
                best_n = None
                for n in vvectors:
                    if auto_normal_acceptable(n):
                        d = abs_dot(bbox_n, n)
                        if d > best_n_dot:
                            best_n_dot = d
                            best_n = n
                            method = 'O'

    # find best u vector if not already found
    if best_n is not None and best_u is None:
        # first check if any in-shape vanishing points
        # are perpendicular to the normal
        best_u = most_orthogonal_vector(
            best_n, [vvectors[i] for __, i in counts],
            tolerance_dot=0.05)

        # else, find the best u from all vectors
        if best_u is None:
            best_u = most_orthogonal_vector(best_n, vvectors)

    # failure
    if best_u is None or best_n is None:
        return (None, None, 0)

    # ortho-normalize system
    uvn = construct_uvn_frame(
        best_n, best_u, b, flip_to_match_image=True)

    # form uvnb matrix, column major
    uvnb = (
        uvn[0, 0], uvn[1, 0], uvn[2, 0], 0,
        uvn[0, 1], uvn[1, 1], uvn[2, 1], 0,
        uvn[0, 2], uvn[1, 2], uvn[2, 2], 0,
        b[0], b[1], b[2], 1
    )

    return uvnb, method, num_vanishing_lines
