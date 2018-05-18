import os
import json
import random
import tempfile
import datetime
import traceback
import subprocess

from PIL import Image, ImageDraw
from colormath.color_objects import RGBColor
from imagekit.utils import open_image

import scipy
import scipy.misc
import scipy.cluster

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.db.models import F, Q

from common.utils import unique_instance_name, \
    save_obj_attr_file, save_obj_attr_image
from common.geom import complex_polygon_centroid, \
    triangle_point_intersects, segment_point_distance_sq


def parse_vertices(vertices_str):
    """
    Parse vertices stored as a string.

    :param vertices: "x1,y1,x2,y2,...,xn,yn"
    :param return: [(x1,y1), (x1, y2), ... (xn, yn)]
    """
    s = [float(t) for t in vertices_str.split(',')]
    return zip(s[::2], s[1::2])


def parse_segments(segments_str):
    """
    Parse segments stored as a string.

    :param vertices: "v1,v2,v3,..."
    :param return: [(v1,v2), (v3, v4), (v5, v6), ... ]
    """
    s = [int(t) for t in segments_str.split(',')]
    return zip(s[::2], s[1::2])


def parse_triangles(triangles_str):
    """
    Parse a list of vertices.

    :param vertices: "v1,v2,v3,..."
    :return: [(v1,v2,v3), (v4, v5, v6), ... ]
    """
    s = [int(t) for t in triangles_str.split(',')]
    return zip(s[::3], s[1::3], s[2::3])


def polylines_from_segments(segments):
    """
    Group segments into nested polylines.  Points are int indices into a
    vertex list.  Segments can either be a flattened string, or a list of int
    tuples.
    """
    raise NotImplementedError("TODO: test this code")

    if isinstance(segments, basestring):
        s = [int(t) for t in segments.split(',')]
        segments = zip(s[::2], s[1::2])

    # link up all nodes
    nodes = {}
    for (s0, s1) in segments:
        if s0 not in nodes[s0]:
            nodes[s0] = []
        if s1 not in nodes[s1]:
            nodes[s1] = []
        nodes[s0].append(s1)
        nodes[s1].append(s0)

    for l in nodes:
        if len(nodes[l]) > 2:
            raise ValueError("Segments do not form polylines")

    polylines = []
    while nodes:
        polyline = []
        parent = nodes.iter().next()
        while parent in nodes:
            polyline.append(parent)
            children = nodes[parent]
            del nodes[parent]
            for c in children:
                if c != parent and c in nodes:
                    parent = c
                    break
            else:
                break
        polylines.append(polyline)

    return polylines


def bbox_vertices(vertices):
    """
    Return bounding box of this object, i.e. ``(min x, min y, max x, max y)``

    :param vertices: List ``[[x1, y1], [x2, y2]]`` or string
        ``"x1,y1,x2,y2,...,xn,yn"``
    """

    if isinstance(vertices, basestring):
        vertices = parse_vertices(vertices)
    x, y = zip(*vertices)  # convert to two lists
    return (min(x), min(y), max(x), max(y))


def complex_polygon_area(vertices, triangles):
    """
    Returns the area of a complex polygon.

    :param vertices: List ``[[x1, y1], [x2, y2]]`` or string
        ``"x1,y1,x2,y2,...,xn,yn"``

    :param triangles: List ``[[v1, v2, v3], [v1, v2, v3]]`` or string
        ``"v1,v2,v3,v1,v2,v3,..."``, where ``vx`` is an index into the vertices
        list.

    :return: area as float
    """

    if isinstance(vertices, basestring):
        vertices = parse_vertices(vertices)
    if isinstance(triangles, basestring):
        triangles = parse_triangles(triangles)

    # compute the area of all triangles
    area_sum = 0
    for tri in triangles:
        a = vertices[tri[0]]
        b = vertices[tri[1]]
        c = vertices[tri[2]]
        area_sum += abs(a[0] * (
            b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    return 0.5 * area_sum


def mask_simple_polygon(image, vertices):
    """
    Crops out a polygon from an image

    :param image: path or :class:`PIL.Image` instance

    :param vertices: List ``[[x1, y1], [x2, y2]]`` or string
        ``"x1,y1,x2,y2,...,xn,yn"``

    :return: a :class:`PIL.Image`, or ``None`` if the bbox is invalid
    """
    if not image:
        return

    if isinstance(vertices, basestring):
        vertices = parse_vertices(vertices)
    if isinstance(image, basestring):
        image = Image.open(image)

    # scale up to size
    w, h = image.size
    vertices = [(int(x * w), int(y * h)) for (x, y) in vertices]

    bbox = bbox_vertices(vertices)
    if (len(vertices) < 3 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]):
        return None

    # crop and shift vertices
    image = image.crop(bbox)
    vertices = [(x - bbox[0], y - bbox[1]) for (x, y) in vertices]

    # draw polygon
    poly = Image.new(mode='RGBA', size=image.size, color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(poly)
    draw.polygon(
        vertices, fill=(255, 255, 255, 255), outline=(255, 255, 255, 255))
    del draw

    # anchor
    dim = max(image.size)
    x, y = (dim - image.size[0]) // 2, (dim - image.size[1]) // 2

    # paste into return value image
    ret = Image.new(mode='RGBA', size=(dim, dim), color=(255, 255, 255, 0))
    ret.paste(image, (x, y), mask=poly)
    return ret


def mask_complex_polygon(image, vertices, triangles, bbox_only=False):
    """
    Crops out a complex polygon from an image.  The returned image is cropped
    to the bounding box of the vertices.

    :param image: path or :class:`PIL.Image`

    :param vertices: List ``[[x1, y1], [x2, y2]]`` or string
        ``"x1,y1,x2,y2,...,xn,yn"``

    :param triangles: List ``[[v1, v2, v3], [v1, v2, v3]]`` or string
        ``"v1,v2,v3,v1,v2,v3,..."``, where ``vx`` is an index into the vertices
        list.

    :param bbox_only: if True, then only the bbox image is returned

    :return: a tuple (masked PIL image, bbox crop PIL image), or None if the bbox is invalid
    """

    if not image:
        return

    if isinstance(vertices, basestring):
        vertices = parse_vertices(vertices)
    if isinstance(triangles, basestring):
        triangles = parse_triangles(triangles)
    if isinstance(image, basestring):
        image = Image.open(image)

    # scale up to size
    w, h = image.size
    vertices = [(int(x * w), int(y * h)) for (x, y) in vertices]

    bbox = bbox_vertices(vertices)
    if (len(vertices) < 3 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]):
        return None

    # crop and shift vertices
    image = image.crop(bbox)
    if bbox_only:
        return image

    vertices = [(x - bbox[0], y - bbox[1]) for (x, y) in vertices]

    # draw triangles
    poly = Image.new(mode='RGBA', size=image.size, color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(poly)
    for tri in triangles:
        points = [vertices[tri[t]] for t in (0, 1, 2)]
        draw.polygon(
            points, fill=(255, 255, 255, 255), outline=(255, 255, 255, 255))
    del draw

    # anchor
    dim = max(image.size)
    x, y = (dim - image.size[0]) // 2, (dim - image.size[1]) // 2

    # paste into return value image
    ret = Image.new(mode='RGBA', size=(dim, dim), color=(255, 255, 255, 0))
    ret.paste(image, (x, y), mask=poly)
    return ret, image


def render_full_complex_polygon_mask(
        vertices, triangles, width, height, inverted=False):
    """
    Returns a black-and-white PIL image (mode ``1``) of size ``width`` x
    ``height``.  The image is not cropped to the bounding box of the vertices.
    Pixels inside the polygon are ``1`` and pixels outside are
    ``0`` (unless ``inverted=True``).

    :param vertices: List ``[[x1, y1], [x2, y2]]`` or string
        ``"x1,y1,x2,y2,...,xn,yn"``

    :param triangles: List ``[[v1, v2, v3], [v1, v2, v3]]`` or string
        ``"v1,v2,v3,v1,v2,v3,..."``, where ``vx`` is an index into the vertices
        list.

    :param width: width of the output mask

    :param height: height of the output mask

    :param inverted: if ``True``, swap ``0`` and ``1`` in the output.

    :return: PIL image of size (width, height)
    """

    if isinstance(vertices, basestring):
        vertices = parse_vertices(vertices)
    if isinstance(triangles, basestring):
        triangles = parse_triangles(triangles)

    if inverted:
        fg, bg = 0, 1
    else:
        fg, bg = 1, 0

    # scale up to size
    vertices = [(int(x * width), int(y * height)) for (x, y) in vertices]

    # draw triangles
    poly = Image.new(mode='1', size=(width, height), color=bg)
    draw = ImageDraw.Draw(poly)
    for tri in triangles:
        points = [vertices[tri[t]] for t in (0, 1, 2)]
        draw.polygon(points, fill=fg, outline=fg)
    del draw

    return poly


def get_dominant_image_colors(image, num_clusters=4):
    """
    Returns the dominant image color that isn't pure white or black.  Uses
    kmeans on the colors.  Returns the result as RGB hex strings in the format
    ['#rrggbb', '#rrggbb', ...].

    :param image: PIL image or path
    """

    if isinstance(image, basestring):
        image = Image.open(image)

    # downsample for speed
    im = image.resize((512, 512), Image.ANTIALIAS)

    # reshape
    ar0 = scipy.misc.fromimage(im)
    shape = ar0.shape
    npixels = scipy.product(shape[:2])
    ar0 = ar0.reshape(npixels, shape[2])

    # keep only nontransparent elements
    ar = ar0[ar0[:, 3] == 255][:, 0:3]

    try:
        # kmeans clustering
        codes, dist = scipy.cluster.vq.kmeans(ar, num_clusters)
    except:
        # kmeans sometimes fails -- if that is the case, use the mean color and
        # nothing else.
        arf = ar.astype(float)
        clamp = lambda p: max(0, min(255, int(p)))
        return ['#' + ''.join(['%0.2x' % clamp(arf[:, i].sum() / float(arf.shape[1])) for i in (0, 1, 2)])]

    vecs, dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
    counts, bins = scipy.histogram(vecs, len(codes))    # count occurrences

    # sort by count frequency
    indices = [i[0] for i in
               sorted(enumerate(counts), key=lambda x:x[1], reverse=True)]

    # convert to hex strings
    colors = [''.join(chr(c) for c in code).encode('hex') for code in codes]

    results = []
    for idx in indices:
        color = colors[idx]
        if color != 'ffffff' and color != '000000':
            results.append('#' + color)

    return results


def update_shape_dominant_rgb(shape, save=True):
    """ Updates the dominant_* fields in a shape instance """

    h = []
    try:
        h = get_dominant_image_colors(open_image(shape.image_crop))
    except:
        print 'Could not find dominant colors for: %s' % shape
        traceback.print_exc()
        return

    if len(h) < 1:
        return

    shape.dominant_rgb0 = h[0]
    shape.dominant_rgb1 = h[1] if len(h) > 1 else ''
    shape.dominant_rgb2 = h[2] if len(h) > 2 else ''
    shape.dominant_rgb3 = h[3] if len(h) > 3 else ''

    shape.dominant_r = float(int(h[0][1:3], 16)) / 255.0
    shape.dominant_g = float(int(h[0][3:5], 16)) / 255.0
    shape.dominant_b = float(int(h[0][5:7], 16)) / 255.0

    print '%s: dominant colors: %s %s %s %s' % (
        shape, shape.dominant_rgb0, shape.dominant_rgb1, shape.dominant_rgb2, shape.dominant_rgb3)

    if save:
        shape.save()


def update_shape_dominant_delta(shape, save=True):
    """ Update shape dominant_delta """

    if not shape.dominant_rgb0 or not shape.dominant_rgb1:
        return

    c0 = RGBColor()
    c1 = RGBColor()
    c0.set_from_rgb_hex(shape.dominant_rgb0)
    c1.set_from_rgb_hex(shape.dominant_rgb1)
    shape.dominant_delta = c0.delta_e(c1)

    if save:
        shape.save()


def update_shape_image_crop(shape, save=True):
    """ Update the cropped image for a shape """

    # compute masked image
    photo = shape.photo.__class__.objects.get(id=shape.photo.id)
    image_crop, image_bbox = mask_complex_polygon(
        image=open_image(photo.image_orig),
        vertices=shape.vertices,
        triangles=shape.triangles)

    if image_crop:
        save_obj_attr_image(shape, attr='image_crop', img=image_crop, format='png', save=save)
        shape.image_square_300.generate()
    if image_bbox:
        save_obj_attr_image(shape, attr='image_bbox', img=image_bbox, format='jpg', save=save)
        shape.image_bbox_1024.generate()


def update_shape_image_pbox(shape, padding=0.25, save=True):
    """ Update the pbox image for a shape """

    # load image
    photo = shape.photo.__class__.objects.get(id=shape.photo.id)
    image = open_image(photo.image_orig)
    w, h = image.size

    # compute bbox
    vertices = [(v[0] * w, v[1] * h) for v in parse_vertices(shape.vertices)]
    bbox = bbox_vertices(vertices)
    if (len(vertices) < 3 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]):
        return None

    # compute pbox
    padding_x = (bbox[2] - bbox[0]) * padding
    padding_y = (bbox[3] - bbox[1]) * padding
    pbox = [
        max(0, bbox[0] - padding_x),
        max(0, bbox[1] - padding_y),
        min(w, bbox[2] + padding_x),
        min(h, bbox[3] + padding_y),
    ]

    # make square
    if pbox[3] - pbox[1] > pbox[2] - pbox[0]:
        mid_x = 0.5 * (pbox[2] + pbox[0])
        half_h = 0.5 * (pbox[3] - pbox[1])
        pbox[0] = mid_x - half_h
        pbox[2] = mid_x + half_h
        if pbox[0] < 0:
            pbox[2] = min(w, pbox[2] - pbox[0])
            pbox[0] = 0
        elif pbox[2] > w:
            pbox[0] = max(0, pbox[0] - (pbox[2] - w))
            pbox[2] = w
    else:
        mid_y = 0.5 * (pbox[3] + pbox[1])
        half_w = 0.5 * (pbox[2] - pbox[0])
        pbox[1] = mid_y - half_w
        pbox[3] = mid_y + half_w
        if pbox[1] < 0:
            pbox[3] = min(h, pbox[3] - pbox[1])
            pbox[1] = 0
        elif pbox[3] > h:
            pbox[1] = max(0, pbox[1] - (pbox[3] - h))
            pbox[3] = h

    # crop image
    image_pbox = image.crop([int(v) for v in pbox])
    if image_pbox:
        shape.pbox = json.dumps([
            float(pbox[0]) / w,
            float(pbox[1]) / h,
            float(pbox[2]) / w,
            float(pbox[3]) / h,
        ])
        # pbox is in units of pixels, so this gives the pixel ratio
        shape.pbox_aspect_ratio = float(pbox[2] - pbox[0]) / float(pbox[3] - pbox[1])
        #print 'bbox: %s, pbox: %s' % (bbox, pbox)
        save_obj_attr_image(shape, attr='image_pbox',
                            img=image_pbox, format='jpg', save=save)
        shape.image_pbox_300.generate()
        shape.image_pbox_512.generate()


def update_shape_three(shape, save=True):
    if not os.path.isfile(settings.CONVERT_OBJ_THREE_BIN):
        raise RuntimeError("ERROR: '%s' (settings.CONVERT_OBJ_THREE_BIN) "
                           "does not exist -- check that it was installed" % (
                               settings.CONVERT_OBJ_THREE_BIN))

    tmpdir = tempfile.mkdtemp()

    try:
        filebase = unique_instance_name(shape)
        pathbase = os.path.join(tmpdir, filebase)

        # convert to OBJ format
        with open(pathbase + '.obj', 'w') as f:
            w_over_h = shape.photo.aspect_ratio
            verts = parse_vertices(shape.vertices)
            #avg_x = sum([v[0] for v in verts]) / float(len(verts))
            #avg_y = sum([v[1] for v in verts]) / float(len(verts))
            for v in verts:
                f.write('v %f %f 1.0\n' % (v[0] * w_over_h, v[1]))
                f.write('vt %f %f\n' % (v[0], 1.0 - v[1]))
            for t in parse_triangles(shape.triangles):
                f.write('f %d/%d %d/%d %d/%d\n' % (
                    t[0] + 1, t[0] + 1,
                    t[1] + 1, t[1] + 1,
                    t[2] + 1, t[2] + 1)
                )

        # convert to THREE.js format
        subprocess.check_call(args=[
            'python', settings.CONVERT_OBJ_THREE_BIN,
            '-i', filebase + '.obj',
            '-o', filebase + '.js',
            '-t', 'binary',
            '-d', 'normal',
        ], cwd=tmpdir)

        # delete any existing files
        if shape.three_bin:
            try:
                os.remove(shape.three_bin.path)
            except OSError as e:
                print e
        if shape.three_js:
            try:
                os.remove(shape.three_js.path)
            except OSError as e:
                print e

        # make sure both files get put in the same directory
        time = datetime.datetime.now()

        # save bin first
        save_obj_attr_file(shape, 'three_bin', filebase + '.bin',
                           content=File(open(pathbase + '.bin')),
                           time=time, save=False)

        # update dict to point to true bin filename
        data = json.loads(open(pathbase + '.js').read())
        data['buffers'] = os.path.basename(shape.three_bin.path)

        # save json dict with updated info
        save_obj_attr_file(shape, 'three_js', filebase + '.js',
                           content=ContentFile(json.dumps(data)),
                           time=time, save=False)

        if save:
            shape.save()

    finally:
        import shutil
        shutil.rmtree(tmpdir)


def update_shape_label_pos(shape, save=True):
    vertices = parse_vertices(shape.vertices)
    triangle_indices = parse_triangles(shape.triangles)
    segment_indices = parse_segments(shape.segments)

    # collect candidate points -- use centroid of entire shape and
    # of each sub-triangle

    candidate_points = []
    centroid = complex_polygon_centroid(vertices, triangle_indices)
    if (any(triangle_point_intersects(
            vertices[a], vertices[b], vertices[c], centroid)
            for (a, b, c) in triangle_indices)):
        candidate_points.append(centroid)

    for t in triangle_indices:
        a, b, c = [vertices[i] for i in t]
        candidate_points.append((
            (a[0] + b[0] + c[0]) / 3.0,
            (a[1] + b[1] + c[1]) / 3.0
        ))

    # find point furthest away from the segments
    best_point = None
    best_d = 0
    for p in candidate_points:
        d = 1e10
        for s0, s1 in segment_indices:
            a, b = vertices[s0], vertices[s1]
            d = min(d, segment_point_distance_sq(
                a[0], a[1], b[0], b[1], p[0], p[1]))
            if d < best_d:
                continue
        if d > best_d:
            best_d = d
            best_point = p

    if best_point:
        shape.label_pos_x = best_point[0]
        shape.label_pos_y = best_point[1]
        if save:
            shape.save()
    else:
        print "Error finding best_point for shape %s" % shape


def get_similar_shapes(bsdf, k=12, dE=20.0, dc=0.5):
    """
    Find ``k`` similar shapes to the given `bsdf`.  The color must be within
    ``dE`` and the gloss contrast must be within ``dc``.

    :param bsdf: instance of :class:`bsdf.models.ShapeBsdfLabel_wd`.
    :param dE: tolerance for Lab color distance
    :param dc: tolerance for gloss contrast

    :return: list of :class:`shape.models.MaterialShape` instances.
    """
    from shapes.models import MaterialShape
    from bsdfs.models import ShapeBsdfLabel_wd

    bsdf_shape = bsdf.shape
    bsdf_shape_substance = bsdf_shape.substance
    bsdf_shape_name = bsdf_shape.name

    qset = ShapeBsdfLabel_wd.objects.filter(
        #shape__photo__scene_category=bsdf.shape.photo.scene_category,
        #shape__photo__license__publishable=True,
        shape__photo__inappropriate=False,
        shape__correct=True,
        color_L__gte=bsdf.color_L - dE,
        color_L__lte=bsdf.color_L + dE,
        color_a__gte=bsdf.color_a - dE,
        color_a__lte=bsdf.color_a + dE,
        color_b__gte=bsdf.color_b - dE,
        color_b__lte=bsdf.color_b + dE,
        contrast__gte=bsdf.contrast - dc,
        contrast__lte=bsdf.contrast + dc,
        shape__bsdf_wd_id=F('id'),
    )

    # filter by name if available
    if bsdf_shape_substance and not bsdf_shape_substance.fail:
        qset = qset.filter(
            Q(shape__substance=bsdf_shape_substance) | Q(shape__substance__isnull=True))
    if bsdf_shape_name and not bsdf_shape_name.fail:
        qset = qset.filter(
            Q(shape__name=bsdf_shape_name) | Q(shape__name__isnull=True))

    bsdfs = qset.order_by('-shape__num_vertices').exclude(id=bsdf.id)[:64]
    bsdfs = [(b, bsdf.color_distance(b) + bsdf.gloss_distance(b)) for b in bsdfs]
    bsdfs.sort(key=lambda x: x[1])

    # uniquify
    visited = set([bsdf.shape_id])
    shape_ids = []
    for b, dist in bsdfs:
        shape_id = b.shape_id
        if shape_id not in visited:
            shape_ids.append(shape_id)
            visited.add(shape_id)
        if len(shape_ids) >= k:
            break

    shapes = MaterialShape.objects.in_bulk(shape_ids)
    return [shapes[id] for id in shape_ids]


def create_shape_image_sample(shape, sample_width=256, sample_height=256):
    """ Return a centered image sample of the shape, or None if a centered
    box intersects the shape edge """

    from shapes.models import ShapeImageSample
    from common.wavelets import compute_wavelet_feature_vector
    if ShapeImageSample.objects.filter(shape=shape).exists():
        return

    photo = shape.photo.__class__.objects.get(id=shape.photo.id)
    image = open_image(photo.image_2048)
    image_width, image_height = image.size

    triangles = parse_triangles(shape.triangles)
    vertices = [(x * image_width, y * image_height)
                for (x, y) in parse_vertices(shape.vertices)]
    b = bbox_vertices(vertices)

    # make sure box is big enough
    if b[2] - b[0] < sample_width or b[3] - b[1] < sample_height:
        return None

    # try random boxes
    filled = False
    for iters in xrange(1000):
        x = int(random.uniform(b[0] + sample_width / 2, b[2] - sample_width / 2))
        y = int(random.uniform(b[1] + sample_height / 2, b[3] - sample_height / 2))

        box = (x - sample_width / 2, y - sample_height / 2,
               x + sample_width / 2, y + sample_height / 2)
        box = [int(f) for f in box]

        # make sure box is filled entirely
        poly = Image.new(mode='1', size=(box[2] - box[0], box[3] - box[1]), color=0)
        draw = ImageDraw.Draw(poly)
        vertices_shifted = [(x - box[0], y - box[1]) for (x, y) in vertices]
        for tri in triangles:
            points = [vertices_shifted[tri[t]] for t in (0, 1, 2)]
            draw.polygon(points, fill=1)
        del draw
        filled = True
        for p in poly.getdata():
            if p != 1:
                filled = False
                break
        if filled:
            break

    if not filled:
        return None

    # create sample
    sample, created = ShapeImageSample.objects.get_or_create(
        shape=shape, defaults={'bbox': json.dumps(box)})
    if created:
        sample_image = image.crop(box)
        sample.feature_vector = \
            compute_wavelet_feature_vector(sample_image)
        save_obj_attr_image(
            sample, attr='image', img=sample_image, format='jpg', save=True)
    return sample


#def material_shape_svg_url(shape, large):
    #""" Render the shape to SVG and return the URL where it was stored """
    #context = {
        #'entry': shape,
        #'large': large,
    #}
    #s = render_to_response('shape_poly_display.svg', context)
    #suffix = 'large' if large else 'small'
    #return dump_to_static_file(
        #s, filename='%s_%s.svg' % (shape.id, suffix),
        #dirname='shape_poly_display')


#@cacheback(2592000)
#def material_shape_svg_url_large(shape):
    #return material_shape_svg_url(shape, large=True)


#@cacheback(2592000)
#def material_shape_svg_url_small(shape):
    #return material_shape_svg_url(shape, large=False)
