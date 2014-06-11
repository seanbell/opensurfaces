import numpy as np


def floodfill_cluster(points, compare, min_size=1):
    raise NotImplementedError("TODO: test this function")

    N = len(points)
    visited = [False] * N
    clusters = []

    for seed_idx in xrange(N):
        if visited[seed_idx]:
            continue

        visited[seed_idx] = True
        seed = points[seed_idx]
        stack = [seed]
        cluster = [seed]

        while stack:
            p = stack.pop()

            for idx in xrange(N):
                if visited[idx]:
                    continue

                q = points[idx]
                if compare(p, q):
                    stack.append(q)
                    cluster.append(q)
                    visited[idx] = True

        if len(cluster) >= min_size:
            clusters.append(cluster)

    return clusters
