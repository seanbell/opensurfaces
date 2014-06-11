import math
import numpy as np


def sample_poisson_uniform(width, height, r, k=30, n_seeds=10000, point_filter=None):
    """ Uniform Poisson disk sampling of a rectangle.  This is an
    implementation of "Fast Poisson Disk Sampling in Arbitrary Dimensions"
    (http://www.cs.ubc.ca/~rbridson/docs/bridson-siggraph07-poissondisk.pdf)
    with the code structure inspired by
    http://devmag.org.za/2009/05/03/poisson-disk-sampling/

    point_filter(p): return True if p = (x, y) is allowed; useful for
    restricting the domain.
    """

    cell_size = r / math.sqrt(2)
    r_sq = r ** 2
    nx = int(math.ceil(width / cell_size))
    ny = int(math.ceil(height / cell_size))

    grid = np.empty((nx, ny), dtype=int)
    grid.fill(-1)

    active_list = []
    sample_points = []

    if not point_filter:
        point_filter = lambda p: True

    # helper functions
    def in_rectangle(q):
        return 0 <= q[0] < width and 0 <= q[1] < height

    def random_point_near(p):
        # yes, the non-uniform sampling is intentional
        # it leads to denser packings
        rr = np.random.uniform(r, 2 * r)
        rt = np.random.uniform(0, 2 * math.pi)
        return (rr * math.cos(rt) + p[0], rr * math.sin(rt) + p[1])

    def is_near_sample_index(idx, q):
        if idx != -1:
            p = sample_points[idx]
            return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 < r_sq
        else:
            return False

    def is_near_sample(q):
        x, y = int(q[0] / cell_size), int(q[1] / cell_size)
        if grid[x, y] != -1:
            return True
        window = grid[
            max(x - 2, 0):min(x + 2, nx),
            max(y - 2, 0):min(y + 2, ny)
        ]
        for idx in np.nditer(window):
            if is_near_sample_index(idx, q):
                return True
        return False

    def store_point(q):
        x, y = int(q[0] / cell_size), int(q[1] / cell_size)
        grid[x, y] = len(sample_points)
        sample_points.append(q)
        active_list.append(q)

    for _ in xrange(n_seeds + 1):
        # seed with new points
        q = np.random.uniform(0, width), np.random.uniform(0, height)
        if point_filter(q) and not is_near_sample(q):
            store_point(q)

        # sample points
        while active_list:
            p = active_list.pop(np.random.randint(len(active_list)))
            for _ in xrange(k):
                q = random_point_near(p)
                if in_rectangle(q) and point_filter(q) and not is_near_sample(q):
                    store_point(q)

    return sample_points
