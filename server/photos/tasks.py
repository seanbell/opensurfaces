import json
import math
import os
import shutil
import subprocess
import tempfile

import numpy as np
from celery import shared_task
from django.db.models import Q, Sum
from PIL import Image, ImageDraw

from common.geom import (abs_dot, homo_line, normalized_cross, sphere_to_unit,
                         unit_to_sphere)
from common.http import download
from common.utils import progress_bar
from imagekit.utils import open_image, save_image
from licenses.models import License
from photos.add import add_photo
from photos.models import FlickrUser, Photo
from pilkit.processors import ResizeToFit
from pilkit.utils import extension_to_format
from pyquery import PyQuery as pq


@shared_task(queue='local_server')
def add_photo_task(*args, **kwargs):
    add_photo(*args, **kwargs)


@shared_task
def update_photo_license(photo_id):
    p = Photo.objects.get(id=photo_id)
    p.license = License.get_for_flickr_photo(p.flickr_user, p.flickr_id)
    p.save()


@shared_task
def update_flickr_users(ids, show_progress=False):
    """ Scrape Flickr for information about Flickr User profiles.

    :param ids: list of database ids (not Flick usernames)
    """

    values = FlickrUser.objects \
        .filter(id__in=ids) \
        .values_list('id', 'username')

    if show_progress:
        values = progress_bar(values)

    for (id, username) in values:
        html = download('https://www.flickr.com/people/%s/' % username)
        if not html:
            continue

        d = pq(html)

        profile = d('div.profile-section')
        given_name = profile('span.given-name').text().strip()
        family_name = profile('span.family-name').text().strip()
        website_name = profile('a.url').text().strip()
        website_url = profile('a.url').attr('href')
        if website_url:
            website_url = website_url.strip()
        else:
            website_url = ""

        person = d('div.person')
        display_name = person('span.character-name-holder').text().strip()
        sub_name = person('h2').text().strip()

        FlickrUser.objects.filter(id=id).update(
            display_name=display_name,
            sub_name=sub_name,
            given_name=given_name,
            family_name=family_name,
            website_name=website_name,
            website_url=website_url,
        )

        if show_progress:
            print '%s: display: "%s" (%s), name: "%s" "%s", web: "%s" (%s)' % (
                username, display_name, sub_name, given_name, family_name,
                website_name, website_url)


@shared_task
def update_photos_num_shapes(photo_ids):
    from shapes.models import MaterialShape
    for photo_id in photo_ids:
        num_shapes = (
            MaterialShape.objects.filter(photo_id=photo_id)
            .filter(**MaterialShape.DEFAULT_FILTERS).count())
        if not num_shapes:
            num_shapes = 0

        num_vertices = (
            MaterialShape.objects.filter(photo_id=photo_id)
            .filter(**MaterialShape.DEFAULT_FILTERS)
            .aggregate(s=Sum('num_vertices'))['s'])
        if not num_vertices:
            num_vertices = 0

        Photo.objects.filter(id=photo_id).update(
            num_shapes=num_shapes,
            num_vertices=num_vertices,
        )


@shared_task
def update_photos_num_intrinsic(photo_ids, show_progress=False):
    from intrinsic.models import IntrinsicPoint, \
        IntrinsicPointComparison, IntrinsicImagesDecomposition
    iterator = progress_bar(photo_ids) if show_progress else photo_ids
    for photo_id in iterator:
        num_comparisons = IntrinsicPointComparison.objects \
            .filter(photo_id=photo_id) \
            .filter(Q(darker__isnull=False, darker_score__gt=0) |
                    Q(darker_method='A')) \
            .count()
        num_points = IntrinsicPoint.objects \
            .filter(photo_id=photo_id) \
            .count()
        errors = IntrinsicImagesDecomposition.objects \
            .filter(photo_id=photo_id,
                    algorithm__active=True,
                    mean_sum_error__isnull=False) \
            .values_list('mean_error')
        if errors:
            median_intrinsic_error = np.median(errors)
        else:
            median_intrinsic_error = None
        Photo.objects.filter(id=photo_id).update(
            num_intrinsic_comparisons=num_comparisons,
            num_intrinsic_points=num_points,
            median_intrinsic_error=median_intrinsic_error,
        )


@shared_task
def detect_vanishing_points(photo_id, dim=800):
    """ Detects vanishing points for a photo and stores it in the database in
    the photo model. """

    # load photo
    photo = Photo.objects.get(id=photo_id)
    orig_image = open_image(photo.image_2048)

    old_vanishing_lines = photo.vanishing_lines
    old_vanishing_points = photo.vanishing_points
    old_vanishing_length = photo.vanishing_length

    detect_vanishing_points_impl(
        photo, ResizeToFit(dim, dim).process(orig_image),
        save=False)

    if old_vanishing_length > photo.vanishing_length:
        photo.vanishing_lines = old_vanishing_lines
        photo.vanishing_points = old_vanishing_points
        photo.vanishing_length = old_vanishing_length

    if photo.vanishing_length:
        photo.save()


def detect_vanishing_points_impl(photo, image, save=True):

    # algorithm parameters
    max_em_iter = 0  # if 0, don't do EM
    min_cluster_size = 10
    min_line_len2 = 4.0
    residual_stdev = 0.75
    max_clusters = 8
    outlier_weight = 0.2
    weight_clamp = 0.1
    lambda_perp = 1.0
    verbose = False

    width, height = image.size
    print 'size: %s x %s' % (width, height)

    vpdetection_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.pardir, os.pardir, 'opt', 'vpdetection', 'matlab'
    ))

    tmpdir = tempfile.mkdtemp()
    try:

        # save image to local tmpdir
        localname = os.path.join(tmpdir, 'image.jpg')
        with open(tmpdir + '/image.jpg', 'wb') as target:
            save_image(image, target, format='JPEG', options={'quality': 90})

        # detect line segments using LSD (Grompone, G., Jakubowicz, J., Morel,
        # J. and Randall, G. (2010). LSD: A Fast Line Segment Detector with a
        # False Detection Control. IEEE Transactions on Pattern Analysis and
        # Machine Intelligence, 32, 722.)
        linesname = os.path.join(tmpdir, 'lines.txt')
        matlab_command = ";".join([
            "try",
            "addpath('../lsd-1.5/')",
            "lines = lsd(double(rgb2gray(imread('%s'))))" % localname,
            "save('%s', 'lines', '-ascii', '-tabs')" % linesname,
            "catch",
            "end",
            "quit",
        ])
        print 'matlab command: %s' % matlab_command
        subprocess.check_call(args=[
            'matlab', '-nodesktop', '-nosplash', '-nodisplay',
            '-r', matlab_command
        ], cwd=vpdetection_dir)

        # cluster lines using J-linkage (Toldo, R. and Fusiello, A. (2008).
        # Robust multiple structures estimation with J-Linkage. European
        # Conference on Computer Vision(ECCV), 2008.)
        # and (Tardif J.-P., Non-iterative Approach for Fast and Accurate
        # Vanishing Point Detection, 12th IEEE International Conference on
        # Computer Vision, Kyoto, Japan, September 27 - October 4, 2009.)
        clustername = os.path.join(tmpdir, 'clusters.txt')
        subprocess.check_call(
            args=['./vpdetection', linesname, clustername],
            cwd=vpdetection_dir)

        # collect line clusters
        clusters_dict = {}
        all_lines = []
        for row in open(clustername, 'r').readlines():
            cols = row.split()
            idx = int(cols[4])
            line = [float(f) for f in cols[0:4]]

            # discard small lines
            x1, y1, x2, y2 = line
            len2 = (x1 - x2) ** 2 + (y2 - y1) ** 2
            if len2 < min_line_len2:
                continue

            if idx in clusters_dict:
                clusters_dict[idx].append(line)
                all_lines.append(line)
            else:
                clusters_dict[idx] = [line]

    finally:
        shutil.rmtree(tmpdir)

    # discard invalid clusters and sort by cluster length
    thresh = 3 if max_em_iter else min_cluster_size
    clusters = filter(lambda x: len(x) >= thresh, clusters_dict.values())
    clusters.sort(key=line_cluster_length, reverse=True)
    if max_em_iter and len(clusters) > max_clusters:
        clusters = clusters[:max_clusters]
    print "Using %s clusters and %s lines" % (len(clusters), len(all_lines))
    if not clusters:
        print "Not enough clusters"
        return

    # Solve for optimal vanishing point using V_GS in 5.2 section of
    # (http://www-etud.iro.umontreal.ca/~tardif/fichiers/Tardif_ICCV2009.pdf).
    # where "optimal" minimizes algebraic error.
    vectors = []
    for lines in clusters:
        # Minimize 'algebraic' error to get an initial solution
        A = np.zeros((len(lines), 3))
        for i in xrange(0, len(lines)):
            x1, y1, x2, y2 = lines[i]
            A[i, :] = [y1 - y2, x2 - x1, x1 * y2 - y1 * x2]
        __, __, VT = np.linalg.svd(A, full_matrices=False, compute_uv=True)
        if VT.shape != (3, 3):
            raise ValueError("Invalid SVD shape (%s)" % VT.size)
        x, y, w = VT[2, :]
        p = [x / w, y / w]
        v = photo.vanishing_point_to_vector(
            (p[0] / width, p[1] / height)
        )
        vectors.append(v)

    # EM
    if max_em_iter:

        # complete orthonormal system
        if len(vectors) >= 2:
            vectors.append(normalized_cross(vectors[0], vectors[1]))

        ### EM refinement ###

        x0 = None
        x_opt = None
        exp_coeff = 0.5 / (residual_stdev ** 2)

        num_weights_nnz = 0
        num_weights = 0

        for em_iter in xrange(max_em_iter):

            ### E STEP ###

            # convert back to vanishing points
            points = vectors_to_points(photo, image, vectors)

            # last column is the outlier cluster
            weights = np.zeros((len(all_lines), len(vectors) + 1))

            # estimate weights (assume uniform prior)
            for i_p, p in enumerate(points):
                weights[:, i_p] = [line_residual(l, p) for l in all_lines]
            weights = np.exp(-exp_coeff * np.square(weights))

            # outlier weight
            weights[:, len(points)] = outlier_weight

            # normalize each row (each line segment) to have unit sum
            weights_row_sum = weights.sum(axis=1)
            weights /= weights_row_sum[:, np.newaxis]

            # add sparsity
            weights[weights < weight_clamp] = 0
            num_weights += weights.size
            num_weights_nnz += np.count_nonzero(weights)

            # check convergence
            if (em_iter >= 10 and len(x0) == len(x_opt) and
                    np.linalg.norm(np.array(x0) - np.array(x_opt)) <= 1e-5):
                break

            # sort by weight
            if len(vectors) > 1:
                vectors_weights = [
                    (v, weights[:, i_v].sum()) for i_v, v in enumerate(vectors)
                ]
                vectors_weights.sort(key=lambda x: x[1], reverse=True)
                vectors = [x[0] for x in vectors_weights]

            ### M STEP ###

            # objective function to minimize
            def objective_function(x, *args):
                cur_vectors = unpack_x(x)
                cur_points = vectors_to_points(photo, image, cur_vectors)

                # line-segment errors
                residuals = [
                    weights[i_l, i_p] * line_residual(all_lines[i_l], p)
                    for i_p, p in enumerate(cur_points)
                    for i_l in np.flatnonzero(weights[:, i_p])
                ]

                # penalize deviations from 45 or 90 degree angles
                if lambda_perp:
                    residuals += [
                        lambda_perp * math.sin(4 * math.acos(abs_dot(v, w)))
                        for i_v, v in enumerate(cur_vectors)
                        for w in cur_vectors[:i_v]
                    ]

                return residuals

            # slowly vary parameters
            t = min(1.0, em_iter / 20.0)

            # vary tol from 1e-2 to 1e-6
            tol = math.exp(math.log(1e-2) * (1 - t) + math.log(1e-6) * t)

            from scipy.optimize import leastsq
            x0 = pack_x(vectors)
            x_opt, __ = leastsq(objective_function, x0, ftol=tol, xtol=tol)
            vectors = unpack_x(x_opt)

            ### BETWEEN ITERATIONS ###

            if verbose:
                print 'EM: %s iters, %s clusters, weight sparsity: %s%%' % (
                    em_iter, len(vectors), 100.0 * num_weights_nnz / num_weights)
                print 'residual: %s' % sum(y ** 2 for y in objective_function(x_opt))

            # complete orthonormal system if missing
            if len(vectors) == 2:
                vectors.append(normalized_cross(vectors[0], vectors[1]))

            # merge similar clusters
            cluster_merge_dot = math.cos(math.radians(t * 20.0))
            vectors_merged = []
            for v in vectors:
                if (not vectors_merged or
                        all(abs_dot(v, w) < cluster_merge_dot for w in vectors_merged)):
                    vectors_merged.append(v)
            if verbose and len(vectors) != len(vectors_merged):
                print 'Merging %s --> %s vectors' % (len(vectors), len(vectors_merged))
            vectors = vectors_merged

        residual = sum(r ** 2 for r in objective_function(x_opt))
        print 'EM: %s iters, residual: %s, %s clusters, weight sparsity: %s%%' % (
            em_iter, residual, len(vectors), 100.0 * num_weights_nnz / num_weights)

        # final points
        points = vectors_to_points(photo, image, vectors)

        # sanity checks
        assert len(vectors) == len(points)

        # re-assign clusters
        clusters_points = [([], p) for p in points]
        line_map_cluster = np.argmax(weights, axis=1)
        for i_l, l in enumerate(all_lines):
            i_c = line_map_cluster[i_l]
            if i_c < len(points):
                clusters_points[i_c][0].append(l)

        # throw away small clusters
        clusters_points = filter(
            lambda x: len(x[0]) >= min_cluster_size, clusters_points)

        # reverse sort by cluster length
        clusters_points.sort(
            key=lambda x: line_cluster_length(x[0]), reverse=True)

        # split into two parallel arrays
        clusters = [cp[0] for cp in clusters_points]
        points = [cp[1] for cp in clusters_points]

    else:  # no EM

        for i_v, lines in enumerate(clusters):
            def objective_function(x, *args):
                p = vectors_to_points(photo, image, unpack_x(x))[0]
                return [line_residual(l, p) for l in lines]
            from scipy.optimize import leastsq
            x0 = pack_x([vectors[i_v]])
            x_opt, __ = leastsq(objective_function, x0)
            vectors[i_v] = unpack_x(x_opt)[0]

        # delete similar vectors
        cluster_merge_dot = math.cos(math.radians(20.0))
        vectors_merged = []
        clusters_merged = []
        for i_v, v in enumerate(vectors):
            if (not vectors_merged or
                    all(abs_dot(v, w) < cluster_merge_dot for w in vectors_merged)):
                vectors_merged.append(v)
                clusters_merged.append(clusters[i_v])
        vectors = vectors_merged
        clusters = clusters_merged

        # clamp number of vectors
        if len(clusters) > max_clusters:
            vectors = vectors[:max_clusters]
            clusters = clusters[:max_clusters]

        points = vectors_to_points(photo, image, vectors)

    # normalize to [0, 0], [1, 1]
    clusters_normalized = [[
        [l[0] / width, l[1] / height, l[2] / width, l[3] / height]
        for l in lines
    ] for lines in clusters]

    points_normalized = [
        (x / width, y / height) for (x, y) in points
    ]

    # save result
    photo.vanishing_lines = json.dumps(clusters_normalized)
    photo.vanishing_points = json.dumps(points_normalized)
    photo.vanishing_length = sum(line_cluster_length(c)
                                 for c in clusters_normalized)
    if save:
        photo.save()


# pack vectors into solution vector (x)
def pack_x(vecs):
    x = []
    for v in vecs:
        x += list(unit_to_sphere(v))
    return x


# unpack vectors from current solution (x)
def unpack_x(x):
    return [
        np.array(sphere_to_unit(x[i:i + 2]))
        for i in xrange(0, len(x), 2)
    ]


def vectors_to_points(photo, image, vectors):
    width, height = image.size
    points = [photo.vector_to_vanishing_point(v) for v in vectors]
    return [(p[0] * width, p[1] * height) for p in points]


def line_cluster_length(lines):
    return sum(
        math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        for x1, y1, x2, y2 in lines
    )


def line_residual(l, p):
    """ Returns the distance between an endpoint of l and the line from p to
    the midpoint of l.  Based on Equation (2) of [Tardif, ICCV 2009
    http://www-etud.iro.umontreal.ca/~tardifj/fichiers/Tardif_ICCV2009.pdf] """
    x1, y1, x2, y2 = l
    midpoint = (0.5 * (x1 + x2), 0.5 * (y1 + y2))
    e = homo_line(p, midpoint)
    d = max(1e-4, e[0] ** 2 + e[1] ** 2)
    return (e[0] * x1 + e[1] * y1 + e[2]) / math.sqrt(d)


@shared_task
def do_gist_tmp(pk, s, s2):
    return
    #from photos.management.commands import gist2
    #gist2.do_gist(pk, s, s2)


@shared_task
def download_photo_task(photo_id, filename, format=None, larger_dimension=None):
    """ Downloads a photo and stores it, potentially downsampling it and
    potentially converting formats """

    parent_dir = os.path.dirname(filename)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    photo = Photo.objects.get(id=photo_id)
    if not larger_dimension and not format:
        photo.image_orig.seek(0)
        with open(filename, 'wb') as f:
            shutil.copyfileobj(photo.image_orig, f)
    else:
        if larger_dimension <= 512:
            image = open_image(photo.image_512)
        elif larger_dimension <= 1024:
            image = open_image(photo.image_1024)
        elif larger_dimension <= 2048:
            image = open_image(photo.image_2048)
        else:
            image = open_image(photo.image_orig)

        if max(image.size) > larger_dimension:
            if image.size[0] > image.size[1]:
                image = image.resize((
                    larger_dimension,
                    larger_dimension * image.size[1] / image.size[0]), Image.ANTIALIAS)
            else:
                image = image.resize((
                    larger_dimension * image.size[0] / image.size[1],
                    larger_dimension), Image.ANTIALIAS)

        if not format:
            format = extension_to_format(os.path.splitext(filename).lower())

        image.save(filename, format)


@shared_task
def photo_to_label_image_task(photo_id, color_map, attr='substance', larger_dimension=320,
                              filename=None, format=None, next_task=None):
    """ Returns a PIL image where each pixel corresponds to a label.
    filename: if specified, save the result to this filename with the specified format
    (instead of returning it since PIL objects often can't be pickled)
    next_task: task to start when this finishes
    """

    from shapes.models import MaterialShape
    from shapes.utils import parse_vertices, parse_triangles

    photo = Photo.objects.get(id=photo_id)
    image = open_image(photo.image_orig)
    w, h = image.size

    if w > h:
        size = (larger_dimension, larger_dimension * h / w)
    else:
        size = (larger_dimension * w / h, larger_dimension)

    label_image = Image.new(mode='RGB', size=size, color=(0, 0, 0))
    drawer = ImageDraw.Draw(label_image)

    shapes = MaterialShape.objects \
        .filter(**{
            'photo_id': photo.id,
            attr + '__isnull': False,
        }) \
        .filter(**MaterialShape.DEFAULT_FILTERS) \
        .order_by('-area')

    has_labels = False
    for shape in shapes:
        vertices = parse_vertices(shape.vertices)
        vertices = [(int(x * size[0]), int(y * size[1])) for (x, y) in vertices]

        for tri in parse_triangles(shape.triangles):
            points = [vertices[tri[t]] for t in (0, 1, 2)]
            val = getattr(shape, attr + '_id')
            if val in color_map:
                color = color_map[val]
                drawer.polygon(points, fill=color, outline=None)
                has_labels = True

    if not has_labels:
        return None

    if filename:
        label_image.save(filename, format=format)
        if next_task:
            next_task()
    else:
        return label_image
