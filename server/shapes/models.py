import json
from collections import Counter

from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit, ResizeCanvas

from common.models import EmptyModelBase, ResultBase
from photos.models import Photo
from common.utils import compute_entropy, get_content_tuple, \
    get_opensurfaces_storage
from common.geom import bbox_svg_transform


STORAGE = get_opensurfaces_storage()


##
## Categories
##


class ShapeName(EmptyModelBase):
    """ Object category, e.g. "Kettle", "Cat", ... """

    #: name of the category, e.g. "Kettle", "Cat", ...
    name = models.CharField(max_length=127, unique=True)

    #: (currently not used) an optional parent category, if caregories
    #: are arranged in a tree
    parent = models.ForeignKey('self', blank=True, null=True)

    #: text description of this object category
    description = models.TextField(blank=True)

    #: a shape that can be shown as an example
    representative_shape = models.ForeignKey(
        'MaterialShape', blank=True, null=True)

    #: if True, this is actually a special failure case category
    fail = models.BooleanField(default=False)

    #: values of ``name`` that are considered "fail"
    FAIL_NAMES = ("Not on list", "More than one object", "I can't tell")

    def material_shape_count(self):
        return get_model('shapes', 'MaterialShape').objects.filter(
            pixel_area__gt=Shape.MIN_PIXEL_AREA, correct=True,
            name=self,
        ).count()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-fail', 'name']

    def save(self, *args, **kwargs):
        if self.name in ShapeName.FAIL_NAMES:
            self.fail = True
        super(ShapeName, self).save(*args, **kwargs)


class ShapeSubstance(EmptyModelBase):
    """ Material category, e.g. "wood", "brick", ... """
    name = models.CharField(max_length=127, unique=True)
    parent = models.ForeignKey('self', blank=True, null=True)

    description = models.TextField(blank=True)
    representative_shape = models.ForeignKey(
        'MaterialShape', blank=True, null=True)

    # if True, this is actually a special failure case category
    fail = models.BooleanField(default=False)

    # if True, this is shown as an option for new labels
    active = models.BooleanField(default=False)

    # each substance group corresponds to a different (possibly overlapping)
    # set of potential object names
    group = models.ForeignKey(
        'ShapeSubstanceGroup', blank=True, null=True,
        related_name='substances')

    #: values of ``name`` that are considered "fail"
    FAIL_NAMES = ("Not on list", "More than one material", "I can't tell")

    def material_shape_count(self):
        return get_model('shapes', 'MaterialShape').objects.filter(
            pixel_area__gt=Shape.MIN_PIXEL_AREA, correct=True,
            substance=self,
        ).count()

    def save(self, *args, **kwargs):
        if self.name in ShapeSubstance.FAIL_NAMES:
            self.fail = True
        super(ShapeSubstance, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-fail', 'name']


class ShapeSubstanceGroup(EmptyModelBase):
    """ Grouping of substances; each substance group is assigned a list of
    names that can be used """

    active = models.BooleanField(default=True)
    names = models.ManyToManyField(ShapeName, related_name='substance_groups')

##
## Shapes
##


class Shape(ResultBase):
    """ Abstract parent describing a complex polygon.  Shapes are represented
    as a bag of vertices, triangles, and line segments.  Users submit
    instances of SubmittedShapes, which are then intersected and triangulated
    to form subclasses of Shape. """

    #: min size of a shape
    MIN_PIXEL_AREA = 4096
    #: min size of a shape for rectification
    MIN_PLANAR_AREA = 16384

    #: Vertices format: x1,y1,x2,y2,x3,y3,... (coords are fractions of width/height)
    #: (this format allows easy embedding into javascript)
    vertices = models.TextField()
    #: num_vertices should be equal to len(points.split(','))//2
    num_vertices = models.IntegerField(db_index=True)

    #: Triangles format: p1,p2,p3,p2,p3,p4..., where p_i is an index into
    #: vertices, and p1-p2-p3 is a triangle.  Each triangle is three indices
    #: into points; all triangles are listed together.  This format allows easy
    #: embedding into javascript.
    triangles = models.TextField()
    #: num_triangles should be equal to len(triangles.split(','))//3
    num_triangles = models.IntegerField()

    #: Segments format: "p1,p2,p2,p3,...", where p_i is an index into vertices,
    #: and p1-p2, p2-p3, ... are the line segments.  The segments are unordered.
    #: Each line segment is two indices into points; all segments are listed
    #: together.  This format allows easy embedding into javascript.
    segments = models.TextField()
    #: num_segments should be equal to len(segments.split(','))//2
    num_segments = models.IntegerField()

    ## Line segments re-grouped as poly-lines "[[p1,p2,p3,p4],[p1,p2,p3],...]",
    ## json encoded.  Each p_i is an index into vertices.  This is the exact same
    ## data as the segments field, but with line segments properly grouped.
    #polylines = models.TextField()
    ## Number of unique polylines; should equal len(json.loads(polylines))
    #num_polylines = models.IntegerField()

    #: Area in normalized units.  To get the pixel area, multiply this by the
    #: total photo area.
    area = models.FloatField()

    #: Area in pixels
    pixel_area = models.IntegerField(null=True, db_index=True)

    #: flag to separate out this shape
    synthetic = models.BooleanField(default=False)
    synthetic_slug = models.CharField(max_length=32, blank=True)

    #: if true, enough users voted this to be the correct type of segmentation
    correct = models.NullBooleanField()
    #: further from 0: more confident in assignment of correct
    correct_score = models.FloatField(
        blank=True, null=True, db_index=True)

    #: if true, enough users voted this to be flat
    planar = models.NullBooleanField()
    #: CUBAM score for the planar field.  further from 0: more confident in
    #: assignment of planar.
    planar_score = models.FloatField(blank=True, null=True, db_index=True)
    #: method by which the planar field was set
    PLANAR_METHODS = (('A', 'admin'), ('C', 'CUBAM'), ('M', 'majority vote'))
    planar_method_to_str = dict((k, v) for (k, v) in PLANAR_METHODS)
    planar_method = models.CharField(
        max_length=1, choices=PLANAR_METHODS, blank=True, null=True)

    #: Photo masked by the shape and cropped to the bounding box.  The masked
    #: (excluded) region has pixels that are white with no opacity (ARGB value
    #: (0, 255, 255, 255)).
    image_crop = models.ImageField(
        upload_to='shapes', blank=True, max_length=255, storage=STORAGE)

    #: square thumbnail with whitebackground
    image_square_300 = ImageSpecField(
        [ResizeToFit(300, 300), ResizeCanvas(300, 300, color=(255, 255, 255))],
        source='image_crop', format='JPEG', options={'quality': 90}, cachefile_storage=STORAGE)

    #: bbox: photo cropped out to the bounding box of this shape
    image_bbox = models.ImageField(
        upload_to='bbox', blank=True, max_length=255, storage=STORAGE)

    #: bbox resized to fit in 512x512
    image_bbox_512 = ImageSpecField(
        [ResizeToFit(512, 512)],
        source='image_bbox', format='JPEG', options={'quality': 90}, cachefile_storage=STORAGE)

    #: bbox resized to fit in 1024x1024 (used by opengl widget in rectify task)
    image_bbox_1024 = ImageSpecField(
        [ResizeToFit(1024, 1024)],
        source='image_bbox', format='JPEG', options={'quality': 90}, cachefile_storage=STORAGE)

    #: position to show a label (normalized coordinates)
    label_pos_x = models.FloatField(blank=True, null=True)
    label_pos_y = models.FloatField(blank=True, null=True)

    ## json-encoded array [min x, min y, max x, max y] indicating the position
    ## of the bounding box.  as usual, positions are specified as fractions of
    ## width and height.
    #bbox = models.TextField(blank=True)

    ## bbox width/height aspect ratio
    #bbox_aspect_ratio = models.FloatField(null=True, blank=True)

    #: padded bounding box image.  this is the bounding box, expanded by 25% on
    #: each side (as a fraction of the bbox width,height), and then the smaller
    #: dimension is expanded to as quare.
    image_pbox = models.ImageField(
        upload_to='pbox', blank=True, max_length=255, storage=STORAGE)

    image_pbox_300 = ImageSpecField(
        [ResizeToFit(300, 300)],
        source='image_pbox', format='JPEG', options={'quality': 90},
        cachefile_storage=STORAGE)

    image_pbox_512 = ImageSpecField(
        [ResizeToFit(512, 512)],
        source='image_pbox', format='JPEG', options={'quality': 90},
        cachefile_storage=STORAGE)

    image_pbox_1024 = ImageSpecField(
        [ResizeToFit(1024, 1024)],
        source='image_pbox', format='JPEG', options={'quality': 90},
        cachefile_storage=STORAGE)

    # pbox width/height aspect ratio (as a ratio of pixel lengths)
    pbox_aspect_ratio = models.FloatField(null=True, blank=True)

    # json-encoded array [min x, min y, max x, max y] indicating the position
    # of the padded box.  as usual, positions are specified as fractions of
    # width and height.
    pbox = models.TextField(blank=True)

    ## The THREE.js vertices are re-normalized so that the aspect ratio is
    ## correct.  The x-coordinate is now in units of height, not width.

    ## THREE.js json file
    #three_js = models.FileField(
        #upload_to='three', blank=True, max_length=255)

    ## THREE.js buffer file
    #three_bin = models.FileField(
        #upload_to='three', blank=True, max_length=255)

    # approximate area of the rectified texture (in pixels)
    rectified_area = models.FloatField(null=True, blank=True)

    # dominant color of this shape
    dominant_r = models.FloatField(null=True, blank=True)
    dominant_g = models.FloatField(null=True, blank=True)
    dominant_b = models.FloatField(null=True, blank=True)

    # top 4 dominant colors written as #rrggbb (for easy HTML viewing)
    # (in decreasing order of frequency)
    dominant_rgb0 = models.CharField(max_length=7, blank=True, default='')
    dominant_rgb1 = models.CharField(max_length=7, blank=True, default='')
    dominant_rgb2 = models.CharField(max_length=7, blank=True, default='')
    dominant_rgb3 = models.CharField(max_length=7, blank=True, default='')

    # difference between top two colors
    dominant_delta = models.FloatField(null=True, blank=True)

    def has_fov(self):
        return self.photo.fov > 0

    def publishable(self):
        return self.photo.publishable()

    def image_pbox_height(self, width):
        """ Returns the height of image_pbox_<width> """
        return min(width, width / self.pbox_aspect_ratio)

    def label_pos_x_scaled(self):
        """ Returns the label position normalized by height instead of width
        """
        return self.label_pos_x * self.photo.aspect_ratio

    def label_pos_2_y_512(self):
        return self.label_pos_y + 1.25 * self.photo.font_size_512()

    # helpers for templates
    def image_pbox_height_1024(self):
        return self.image_pbox_height(1024)

    def image_pbox_height_512(self):
        return self.image_pbox_height(512)

    def save(self, *args, **kwargs):
        # compute counts:
        if not self.num_vertices:
            self.num_vertices = len(self.vertices.split(',')) // 2
        if not self.num_triangles:
            self.num_triangles = len(self.triangles.split(',')) // 3
        if not self.num_segments:
            self.num_segments = len(self.segments.split(',')) // 2
        if not self.area:
            from shapes.utils import complex_polygon_area
            self.area = complex_polygon_area(self.vertices, self.triangles)
        if not self.pixel_area:
            self.pixel_area = (self.area * self.photo.image_orig.width *
                               self.photo.image_orig.height)
        if not self.synthetic:
            self.synthetic = self.photo.synthetic
        if not self.label_pos_x or not self.label_pos_y:
            from shapes.utils import update_shape_label_pos
            update_shape_label_pos(self, save=False)

        thumbs_dirty = (not self.id)

        # compute cropped image synchronously, before saving
        # (this way the shape only shows up after all thumbs are available)
        if not self.image_crop or not self.image_bbox:
            from shapes.utils import update_shape_image_crop
            update_shape_image_crop(self, save=False)
            thumbs_dirty = True

        if not self.image_pbox:
            from shapes.utils import update_shape_image_pbox
            update_shape_image_pbox(self, save=False)
            thumbs_dirty = True

        #if not self.three_js or not self.three_bin:
            #from shapes.utils import update_shape_three
            #update_shape_three(self, save=False)

        #if not self.dominant_rgb0:
        if thumbs_dirty:
            from shapes.utils import update_shape_dominant_rgb
            update_shape_dominant_rgb(self, save=False)

        if (not self.dominant_delta and
                self.dominant_rgb0 and
                self.dominant_rgb1):
            from shapes.utils import update_shape_dominant_delta
            update_shape_dominant_delta(self, save=False)

        super(Shape, self).save(*args, **kwargs)

    def render_full_complex_polygon_mask(
            self, width=None, height=None, inverted=False):
        """
        Returns a black-and-white PIL image (mode ``1``) the same size as the
        original photo (unless ``width`` and ``height`` are specified.  Pixels
        inside the polygon are ``1`` and pixels outside are ``0`` (unless
        ``inverted=True``).

        :param width: width in pixels, or if ``None``, use
            ``self.photo.orig_width``.

        :param height: width in pixels, or if ``None``, use
            ``self.photo.orig_height``.

        :param inverted: if ``True``, swap ``0`` and ``1`` in the output.
        """

        from shapes.utils import render_full_complex_polygon_mask
        return render_full_complex_polygon_mask(
            vertices=self.vertices,
            triangles=self.triangles,
            width=width if width else self.photo.orig_width,
            height=height if height else self.photo.orig_height,
            inverted=inverted)

    # temporary hack
    def is_kitchen(self):
        return (self.photo.scene_category.name == u'kitchen')

    # temporary hack
    def is_living_room(self):
        return (self.photo.scene_category.name == u'living room')

    # deprecated -- delete at some point
    def area_pixels(self):
        return (self.area *
                self.photo.image_orig.width *
                self.photo.image_orig.height)

    def __unicode__(self):
        return 'Shape (%s v)' % self.num_vertices

    def segments_svg_path(self):
        """ Returns all line segments as SVG path data """
        verts = self.vertices.split(',')  # leave as string
        segs = [int(v) for v in self.segments.split(',')]
        data = []
        for i in xrange(0, len(segs), 2):
            v0 = 2 * segs[i]
            v1 = 2 * segs[i + 1]
            data.append(u"M%s,%sL%s,%s" % (
                verts[v0], verts[v0 + 1],
                verts[v1], verts[v1 + 1],
            ))
        return u"".join(data)

    def triangles_svg_path(self):
        """ Returns all triangles as SVG path data """
        verts = self.vertices.split(',')  # leave as string
        tris = [int(v) for v in self.triangles.split(',')]
        data = []
        for i in xrange(0, len(tris), 3):
            v0 = 2 * tris[i]
            v1 = 2 * tris[i + 1]
            v2 = 2 * tris[i + 2]
            data.append(u"M%s,%sL%s,%sL%s,%sz" % (
                verts[v0], verts[v0 + 1],
                verts[v1], verts[v1 + 1],
                verts[v2], verts[v2 + 1],
            ))
        return u"".join(data)

    def pbox_view_box(self):
        """ Returns the padded box as the tuple
        ``(min_x, min_y, width, height)`` """
        pbox = json.loads(self.pbox)
        return (pbox[0], pbox[1], pbox[2] - pbox[0], pbox[3] - pbox[0])

    def pbox_svg_transform(self):
        return "scale(%s,1) %s" % (
            self.pbox_aspect_ratio,
            bbox_svg_transform(json.loads(self.pbox)),
        )

    #def shape_svg_url_large(self):
        #from shapes.utils import material_shape_svg_url_large
        #return material_shape_svg_url_large(self)

    #def shape_svg_url_small(self):
        #from shapes.utils import material_shape_svg_url_small
        #return material_shape_svg_url_small(self)

    def get_entry_dict(self):
        """ Return a dictionary of this model containing just the fields needed
        for javascript rendering.  """

        # generating thumbnail URLs is slow, so only generate the ones
        # that will definitely be used.
        ret = {
            'id': self.id,
            'vertices': self.vertices,
            'triangles': self.triangles,
            'segments': self.segments,
            'photo': self.photo.get_entry_dict(),
        }
        if self.dominant_rgb0:
            ret['dominant_rgb0'] = self.dominant_rgb0
        #if self.image_pbox:
            #ret['pbox'] = self.pbox
            #ret['image_pbox'] = {
                #'300': self.image_pbox_300.url,
                #'512': self.image_pbox_512.url,
                #'1024': self.image_pbox_1024.url,
                #'orig': self.image_pbox.url,
            #}
        if self.image_bbox:
            ret['image_bbox'] = {
                #'512': self.image_bbox_512.url,
                '1024': self.image_bbox_1024.url,
                #'orig': self.image_bbox.url,
            }
        return ret

    def mark_invalid(self, *args, **kwargs):
        self.correct = False
        super(Shape, self).mark_invalid(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['-num_vertices', '-time_ms']


class MaterialShape(Shape):
    """ Complex polygon containing a single material.  This is created after a
    SubmittedShape has been triangulated. """

    photo = models.ForeignKey(Photo, related_name='material_shapes')

    #: the submitted shapes that contain this shape
    submitted_shapes = models.ManyToManyField(
        'SubmittedShape', related_name='material_shapes')

    #: majority vote substance
    substance = models.ForeignKey(ShapeSubstance, null=True, blank=True)

    #: disagreement about substance
    substance_entropy = models.FloatField(null=True, blank=True)

    #: CUBAM score for substance
    substance_score = models.FloatField(null=True, blank=True)

    #: majority vote name
    name = models.ForeignKey(ShapeName, null=True, blank=True)

    #: disagreement about name
    name_entropy = models.FloatField(null=True, blank=True)

    #: CUBAM score for name
    name_score = models.FloatField(null=True, blank=True)

    #: Best rectified normal for this shape
    rectified_normal = models.ForeignKey(
        'normals.ShapeRectifiedNormalLabel', null=True, blank=True)

    #: Best reflectance for this shape
    bsdf_wd = models.ForeignKey(
        'bsdfs.ShapeBsdfLabel_wd', null=True, blank=True)

    #: Default filters for views
    DEFAULT_FILTERS = {
        'pixel_area__gt': Shape.MIN_PIXEL_AREA,
        'invalid': False,
        'correct': True,
        'synthetic': False,
        'photo__inappropriate': False,
        'photo__stylized': False,
        'photo__rotated': False,
        'photo__nonperspective': False,
        'photo__scene_category_correct': True,
        'photo__scene_category_correct_score__isnull': False,
    }

    def has_substance(self):
        return self.substance is not None

    def save(self, *args, **kwargs):
        if not self.substance_entropy or not self.name_entropy:
            self.update_entropy(save=False)
        super(MaterialShape, self).save(*args, **kwargs)

    def update_entropy(self, save=True):
        """ Update best label for each type of data """

        #min_consensus = self.mturk_assignment.hit.hit_type \
                #.experiment_settings.min_output_consensus
        min_consensus = 3

        # update substance label and entropy
        self.substance = None
        substances = self.substances.filter(invalid=False) \
            .values_list('substance_id', flat=True)
        if substances:
            self.substance_entropy = compute_entropy(substances)
            hist = Counter(substances).most_common(2)
            substance_id, count = hist[0]
            # must be at least the consensus, and larger than the 2nd choice
            if count >= min_consensus and (len(hist) == 1 or hist[1][1] < count):
                self.substance_id = substance_id
                self.quality_method = 'M'

        # update name label and entropy
        self.name = None
        names = self.names.filter(invalid=False) \
            .values_list('name_id', flat=True)
        if names.exists():
            self.name_entropy = compute_entropy(names)
            hist = Counter(names).most_common(2)
            name_id, count = hist[0]
            # must be at least the consensus, and larger than the 2nd choice
            if count >= min_consensus and (len(hist) == 1 or hist[1][1] < count):
                self.name_id = name_id
                self.quality_method = 'M'

        # update rectified normal
        self.rectified_normal = None
        if self.planar:
            for n in self.rectified_normals.all():
                if n.better_than(self.rectified_normal):
                    self.rectified_normal = n
            if self.rectified_normal and not self.rectified_normal.correct:
                self.rectified_normal = None

        # update bsdf
        self.bsdf_wd = None
        for b in self.bsdfs_wd.all():
            if b.gloss_correct and b.color_correct and b.better_than(self.bsdf_wd):
                self.bsdf_wd = b

        if save:
            self.save()

    def num_material_votes(self):
        """ mturk votes that the shape is a good material segmentation """
        return self.qualities.filter(correct=True).count()

    def num_bad_votes(self):
        """ mturk votes that the shape is a bad segmentation """
        return self.qualities.filter(correct=False).count()

    def num_votes(self):
        """ mturk vote count """
        return self.qualities.count()

    def votes_dict(self):
        """ mturk votes as a python dictionary """
        votes = {'M': 0, 'B': 0}
        for q in self.qualities.all():
            if q.correct:
                votes['M'] += 1
            else:
                votes['B'] += 1
        return votes

    def num_planar_votes(self):
        return self.planarities.filter(planar=True).count()

    def num_nonplanar_votes(self):
        return self.planarities.filter(planar=False).count()

    def num_planarity_votes(self):
        return self.planarities.count()

    def __unicode__(self):
        return 'MaterialShape (%s v, id=%s)' % (self.num_vertices, self.id)

    def get_absolute_url(self):
        return reverse('shapes.views.material_shape_detail', args=[str(self.id)])

    def get_thumb_template(self):
        return 'material_shape_thumb.html'


class SubmittedShape(ResultBase):
    """ Simple polygon submitted by a user (described by a single closed
    poly-line, no holes) """

    photo = models.ForeignKey(Photo, related_name='submitted_shapes')

    # Vertices format: x1,y1,x2,y2,x3,y3,... (coords are fractions of width/height)
    # (this format allows easy embedding into javascript)
    vertices = models.TextField(null=True)
    # num_vertices should be equal to len(points.split(','))//2
    num_vertices = models.IntegerField(null=True)

    # shape type
    SHAPE_TYPES = (('M', 'material'), ('O', 'object'))
    shape_type_to_str = dict((k, v) for (k, v) in SHAPE_TYPES)
    str_to_shape_type = dict((v, k) for (k, v) in SHAPE_TYPES)

    shape_type = models.CharField(max_length=1, choices=SHAPE_TYPES)

    def __unicode__(self):
        return '%s vertices' % self.num_vertices

    def get_thumb_template(self):
        return 'submitted_shape_thumb.html'

    def publishable(self):
        return self.photo.publishable()

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #shapes = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not shapes:
            #return None

        ## reject all-triangle or empty submissions
        #if all(s.num_vertices < 4 for s in shapes):
            #return 1.0

        #tshapes = []
        #for s in shapes:
            #if s.shape_type == 'M':
                #tshapes += s.material_shapes.all()
            #elif s.shape_type == 'O':
                #tshapes += s.object_shapes.all()
            #else:
                #raise ValueError('Error in model')

        ## we can't really say what happened, so we shouldn't reject it
        #if not tshapes:
            #return 0.0

        ## count percentage of bad labels
        #bad = 0
        #for ts in tshapes:
            #if ts.time_ms < 3000:
                #bad += 1
            #elif ts.pixel_area < Shape.MIN_PIXEL_AREA:
                #bad += 0.5
            #elif ts.correct_score is None:
                #return None
            #elif ts.correct_score < -0.5 and ts.time_ms < 30000:
                #bad += 1.0

        #if bad > 0:
            #return float(bad) / float(len(tshapes))

        ## reward good shapes; the negative badness score
        ## becomes a bonus later on
        #return sum(-1.0 for ts in tshapes if
                   #ts.correct_score > 0.5 and
                   #ts.num_vertices > 30 and
                   #ts.time_ms > 30000 and
                   #ts.area > 0.03)

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms,
                     experiment, version, mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: %s" % version)

        photo = hit_contents[0]
        poly_list = results[str(photo.id)]
        time_ms_list = time_ms[str(photo.id)]
        time_active_ms_list = time_active_ms[str(photo.id)]

        if len(poly_list) != len(time_ms_list):
            raise ValueError("Result length mismatch (%s polygons, %s times)" % (
                len(poly_list), len(time_ms_list)))

        shape_model = MaterialShape
        slug = experiment.slug
        if slug == "segment_material":
            shape_type = 'M'
        elif slug == "segment_object":
            shape_type = 'O'
        else:
            raise ValueError("Unknown slug: %s" % slug)

        # store results in SubmittedShape objects
        new_objects_list = []
        for idx in xrange(len(poly_list)):
            poly_vertices = poly_list[idx]
            poly_time_ms = time_ms_list[idx]
            poly_time_active_ms = time_active_ms_list[idx]

            num_vertices = len(poly_vertices)
            if num_vertices % 2 != 0:
                raise ValueError("Odd number of vertices (%d)" % num_vertices)
            num_vertices //= 2

            new_obj, created = photo.submitted_shapes.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=poly_time_ms,
                time_active_ms=poly_time_active_ms,
                # (repr gives more float digits)
                vertices=','.join([repr(f) for f in poly_vertices]),
                num_vertices=num_vertices,
                shape_type=shape_type
            )

            if created:
                new_objects_list.append(new_obj)

        # triangulate polygons (creates instances of shape_model)
        if new_objects_list:
            from shapes.tasks import triangulate_submitted_shapes_task
            triangulate_submitted_shapes_task.delay(
                photo, user, mturk_assignment, shape_model, new_objects_list)

        if new_objects_list:
            return {get_content_tuple(photo): new_objects_list}
        else:
            return {}


##
## Labels
##


class MaterialShapeLabelBase(ResultBase):
    """ Abstract parent for labels attached to material shapes """

    #: vote from admin
    #: -2: reject
    #: -1: can't really tell what's going on
    #: 0: un-voted
    #: 1: good, but missed something (not rotated)
    #: 2: correct
    #: 3: correct exemplar
    admin_score = models.IntegerField(default=0)

    # if false, then the user started working on a label but did not submit
    #complete = models.BooleanField(default=False)

    def publishable(self):
        return self.shape.publishable()

    def get_thumb_template(self):
        return 'material_shape_label_thumb.html'

    class Meta:
        abstract = True
        ordering = ['shape', '-time_ms']


class ShapeSubstanceLabel(MaterialShapeLabelBase):
    """ Material common name, e.g. "Wood", "Brick" """
    shape = models.ForeignKey(MaterialShape, related_name="substances")
    substance = models.ForeignKey(ShapeSubstance, blank=True, null=True)

    def __unicode__(self):
        if self.substance:
            base = self.substance.name
        else:
            return "(Invalid label)"

        if self.mturk_assignment.hit.sandbox:
            return base + " (SB)"
        else:
            return base

    class Meta:
        ordering = ['-substance', '-time_ms']

    def get_thumb_overlay(self):
        return self.__unicode__()

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #total = sum(1 for l in labels if l.shape.substance)
        #if total == 0:
            #return None
        #bad = sum(1 for l in labels if
                  #l.time_ms < 400 or
                  #(l.shape.substance and l.substance != l.shape.substance))
        #return float(bad) / max(float(total), 3)

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}
        if not user:
            raise ValueError("Null user")

        new_objects = {}
        for shape in hit_contents:
            name_string = results[unicode(shape.id)]
            shape_time_ms = time_ms[unicode(shape.id)]
            shape_time_active_ms = time_active_ms[unicode(shape.id)]

            # normalize case
            name_string = name_string.lower()
            name_string = name_string[0].upper() + name_string[1:]

            substance, created = ShapeSubstance.objects.get_or_create(
                name=name_string,
            )

            new_obj, created = shape.substances.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=shape_time_ms,
                time_active_ms=shape_time_active_ms,
                substance=substance)

            if created and substance:
                shape.update_entropy(save=True)
                new_objects[get_content_tuple(shape)] = [new_obj]

        return new_objects


class MaterialShapeNameLabel(MaterialShapeLabelBase):
    """ Object common name, e.g. "chair", "door" """

    #: Shape being labeled
    shape = models.ForeignKey(MaterialShape, related_name="names")

    #: Object name chosen for the shape
    name = models.ForeignKey(ShapeName, blank=True, null=True)

    def __unicode__(self):
        if self.name:
            base = self.name.name
        else:
            return "(Invalid label)"

        if self.mturk_assignment.hit.sandbox:
            return base + " (SB)"
        else:
            return base

    class Meta:
        ordering = ['-name', '-time_ms']

    def get_thumb_overlay(self):
        return self.__unicode__()

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #total = sum(1 for l in labels if l.shape.name)
        #if total == 0:
            #return None
        #bad = sum(1 for l in labels if
                  #l.time_ms < 400 or
                  #(l.shape.name and l.name != l.shape.name))
        #return float(bad) / max(3, float(total))

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}
        if not user:
            raise ValueError("Null user")

        new_objects = {}
        for shape in hit_contents:
            name_string = results[unicode(shape.id)]
            shape_time_ms = time_ms[unicode(shape.id)]
            shape_time_active_ms = time_active_ms[unicode(shape.id)]

            # normalize case
            name_string = name_string.lower()
            name_string = name_string[0].upper() + name_string[1:]

            name = ShapeName.objects.get_or_create(
                name=name_string,
            )[0]

            new_obj, created = shape.names.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=shape_time_ms,
                time_active_ms=shape_time_active_ms,
                name=name)

            if created and name:
                shape.update_entropy(save=True)
                new_objects[get_content_tuple(shape)] = [new_obj]

        return new_objects


class ShapePlanarityLabel(MaterialShapeLabelBase):
    """ Vote for whether or not a material shape is flat """

    shape = models.ForeignKey(MaterialShape, related_name='planarities')
    planar = models.BooleanField(default=False)
    canttell = models.NullBooleanField()

    def __unicode__(self):
        if self.canttell:
            return "can't tell"
        else:
            return 'planar' if self.planar else 'not planar'

    class Meta:
        verbose_name = "Shape planarity label"
        verbose_name_plural = "Shape planarity labels"

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #if any(l.shape.planar_score is None for l in labels):
            #return None
        #bad = sum(1 for l in labels if l.planar != l.shape.planar)
        #return float(bad) / float(len(labels))

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        # best we can do is average
        avg_time_ms = time_ms / len(hit_contents)
        avg_time_active_ms = time_active_ms / len(hit_contents)

        new_objects = {}
        for shape in hit_contents:
            selected = (
                str(results[unicode(shape.id)]['selected']).lower() == 'true')
            canttell = (
                str(results[unicode(shape.id)]['canttell']).lower() == 'true')

            new_obj, created = shape.planarities.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=avg_time_ms,
                time_active_ms=avg_time_active_ms,
                planar=selected,
                canttell=canttell,
            )

            if created:
                new_objects[get_content_tuple(shape)] = [new_obj]

        return new_objects


class MaterialShapeQuality(MaterialShapeLabelBase):
    """ Vote on whether or not a shape is indeed a material or oject segmentation """

    shape = models.ForeignKey(MaterialShape, related_name='qualities')
    correct = models.BooleanField(default=False)
    canttell = models.NullBooleanField()

    def __unicode__(self):
        if self.canttell:
            return "can't tell"
        else:
            return 'correct' if self.correct else 'not correct'

    class Meta:
        verbose_name = "Shape quality vote"
        verbose_name_plural = "Shape quality votes"

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #if any(l.shape.correct_score is None for l in labels):
            #return None
        #bad = sum(1 for l in labels if l.correct != l.shape.correct
                  #and abs(l.shape.correct_score) > 0.5)
        #return float(bad) / float(len(labels))

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        # best we can do is average
        avg_time_ms = time_ms / len(hit_contents)
        avg_time_active_ms = time_active_ms / len(hit_contents)

        new_objects = {}
        for shape in hit_contents:
            selected = (
                str(results[unicode(shape.id)]['selected']).lower() == 'true')
            canttell = (
                str(results[unicode(shape.id)]['canttell']).lower() == 'true')

            new_obj, created = shape.qualities.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=avg_time_ms,
                time_active_ms=avg_time_active_ms,
                correct=selected,
                canttell=canttell,
            )

            if created:
                new_objects[get_content_tuple(shape)] = [new_obj]

        return new_objects
