from intrinsic.models import IntrinsicPointComparison
from collections import defaultdict


def intrinsic_consistent_triangles(photo_id):
    """ Return (consistent weight, inconsistent weight) triangles """

    # triangles
    max_depth = 3

    edges = IntrinsicPointComparison.objects \
        .filter(photo=photo_id, darker__isnull=False, darker_score__gt=0) \
        .values_list('point1_id', 'point2_id', 'darker', 'darker_score')

    if not edges:
        return (0.0, 0.0)

    point_to_neighbors = defaultdict(list)
    for (p1, p2, _, _) in edges:
        point_to_neighbors[p1].append(p2)
        point_to_neighbors[p2].append(p1)

    cycles = set()
    for root_point in point_to_neighbors.keys():
        # [ path, ... ]
        stack = [(root_point, )]

        while stack:
            path = stack.pop()
            depth = len(path)

            if len(path) >= 3 and root_point in point_to_neighbors[path[-1]]:
                # rotate list of points so that smallest point_id is first
                cycles.add(tuple(sorted(path)))
            elif not max_depth or depth < max_depth:
                for neighbor in point_to_neighbors[path[-1]]:
                    if neighbor not in path:
                        stack.append(path + (neighbor, ))

    consistent_weight = 0
    inconsistent_weight = 0

    edge_to_darker = {}
    edge_to_score = {}
    for (p1, p2, d, score) in edges:
        key = (min(p1, p2), max(p1, p2))
        edge_to_score[key] = score
        if d == 'E':
            edge_to_darker[key] = 'E'
        elif d == '1':
            edge_to_darker[key] = p1
        elif d == '2':
            edge_to_darker[key] = p2
        else:
            raise ValueError("Invalid value for darker: %s" % d)

    for (a, b, c) in cycles:
        # three triangle edges
        ab = edge_to_darker[(a, b)]
        ac = edge_to_darker[(a, c)]
        bc = edge_to_darker[(b, c)]

        # total weight of the 3 edges
        weight = (
            edge_to_score[(a, b)] +
            edge_to_score[(a, c)] +
            edge_to_score[(b, c)]
        )

        # number of E edges
        num_equal = sum(1 if d == 'E' else 0 for d in [ab, ac, bc])

        # True if the edge is oriented clockwise
        cw = [
            ab == b,
            bc == c,
            ac == a,
        ]

        if num_equal == 0:
            # 0 E edges: inconsistent only if all oriented the same way
            s = sum(1 if c else 0 for c in cw)
            if s == 0 or s == 3:
                inconsistent_weight += weight
            else:
                consistent_weight += weight
        elif num_equal == 1:
            # 1 E edges: inconsistent only if the non-E edges are oriented the
            # same way
            s = sum(1 if c else 0 for c in cw)
            if s == 0 or s == 2:
                inconsistent_weight += weight
            else:
                consistent_weight += weight
        elif num_equal == 2:
            # 2 E edges: always inconsistent
            inconsistent_weight += weight
        else:
            # 3 E edges: always consistent
            consistent_weight += weight

    return (consistent_weight, inconsistent_weight)


def rotate_list(l, n):
    """ Rotate list l so that index n is now first """
    return l[n:] + l[:n]
