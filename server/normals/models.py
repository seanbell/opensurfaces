import math
import json
import numpy as np

from django.db import models

from imagekit.models import ImageSpecField
from imagekit.processors import SmartResize, ResizeToFit

from common.models import ResultBase
from shapes.models import Shape, MaterialShape, MaterialShapeLabelBase

from common.geom import orthogonalize_matrix
from common.utils import save_obj_attr_image, get_content_tuple, \
    get_opensurfaces_storage


STORAGE = get_opensurfaces_storage()

# unit points in homogenous coordinates
VEC4_X = np.matrix([[1], [0], [0], [1]])
VEC4_Y = np.matrix([[0], [1], [0], [1]])
VEC4_Z = np.matrix([[0], [0], [1], [1]])


class ShapeRectifiedNormalLabel(MaterialShapeLabelBase):
    """
    Surface normal obtained by rectifying a material.

    The normal is described by a 4x4 ``uvnb`` matrix.  The top-left ``uvn``
    matrix is a 3x3 rotation matrix (two vectors ``uv`` in the plane and
    surface normal ``n``), and the rightmost ``b`` column is the origin of the
    plane.
    """

    shape = models.ForeignKey(MaterialShape, related_name='rectified_normals')

    #: if true, this was estimated automatically using vanishing points
    automatic = models.BooleanField(default=False)

    #: which method was used to create this normal
    METHODS = (('T', 'continuous normal (thumbtack)'),
               ('G', 'continuous normal (grid)'),
               ('V', 'vanishing point'),
               ('O', 'VP (object name)'),
               ('A', 'VP (edges in shape)'),
               ('S', 'VP'))
    method_to_str = dict((k, v) for (k, v) in METHODS)
    method = models.CharField(max_length=1, choices=METHODS, blank=True)

    #: 4x4 matrix in column major order, stored as a json array. columns: u axis, v
    #: axis, normal, 3d point on plane (b).
    #:
    #: ::
    #:
    #:     [ 0 4  8 12 ] corresponds to [ u v n b ]
    #:     [ 1 5  9 13 ]
    #:     [ 2 6 10 14 ]
    #:     [ 3 7 11 15 ]
    uvnb = models.TextField()

    #: number of vanishing lines contained in the shape when estimating
    #: vanishing points
    num_vanishing_lines = models.IntegerField(null=True, blank=True)

    #: x position / width  (place that the user was shown to measure)
    pos_x = models.FloatField(null=True, blank=True)
    #: y position / height (place that the user was shown to measure)
    pos_y = models.FloatField(null=True, blank=True)

    #: focal length used to project points
    focal_pixels = models.FloatField(null=True, blank=True)

    #: width of the kinetic.js canvas (only the portion used)
    canvas_width = models.IntegerField(null=True, blank=True)
    #: height of the kinetic.js canvas (only the portion used)
    canvas_height = models.IntegerField(null=True, blank=True)

    #: if true, enough users voted this to be a correct rectification
    correct = models.NullBooleanField()
    #: further from 0: more confident in assignment of correct
    correct_score = models.FloatField(
        blank=True, null=True, db_index=True)

    image_rectified = models.ImageField(
        upload_to='normal-rectified', null=True, blank=True, max_length=255,
        storage=STORAGE,
    )

    image_rectified_1024 = ImageSpecField(
        [ResizeToFit(1024, 2 * 1024)], source='image_rectified',
        format='JPEG', options={'quality': 90},
        cachefile_storage=STORAGE,
    )

    image_rectified_square_300 = ImageSpecField(
        [SmartResize(300, 300)], source='image_rectified',
        format='JPEG', options={'quality': 90},
        cachefile_storage=STORAGE,
    )

    image_rectified_square_512 = ImageSpecField(
        [SmartResize(512, 512)], source='image_rectified',
        format='JPEG', options={'quality': 90},
        cachefile_storage=STORAGE,
    )

    class Meta:
        ordering = ['-admin_score']

    def mark_invalid(self, *args, **kwargs):
        self.correct = False
        super(Shape, self).mark_invalid(*args, **kwargs)

    def __unicode__(self):
        return u'%s deg' % (self.phi_degrees())

    def method_str(self):
        return ShapeRectifiedNormalLabel.method_to_str[self.method]

    def phi_degrees(self):
        # uvnb[10]: z coordinate of normal
        return math.degrees(math.acos(json.loads(self.uvnb)[10]))

    def get_thumb_template(self):
        return 'rectified_normal_thumb.html'

    def u(self):
        """ Returns the horizontal vector (1st column of uvnb matrix) """
        uvnb = json.loads(self.uvnb)
        return (uvnb[0], uvnb[1], uvnb[2])

    def n(self):
        """ Returns the normal vector (3rd column of uvnb matrix) """
        uvnb = json.loads(self.uvnb)
        return (uvnb[8], uvnb[9], uvnb[10])

    def angle_degrees(self, other):
        """ Returns the angle with another normal """
        return math.degrees(math.acos(np.dot(self.n(), other.n())))

    def proj_matrix(self):
        """ Returns the disc --> image transform as a numpy matrix.
        Input domain: disc plane.  Output domain: [0,1]x[0,1] image. """
        if hasattr(self, '_proj_matrix'):
            return self._proj_matrix
        focal_y = self.shape.photo.focal_y
        focal_x = focal_y / self.shape.photo.aspect_ratio
        T = np.matrix([
            [1, 0, 0, 0.5],
            [0, -1, 0, 0.5],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ])
        K = np.matrix([
            [focal_x, 0, 0, 0],
            [0, focal_y, 0, 0],
            [0, 0, 0, 1],
            [0, 0, -1, 0],
        ])
        P = T * K * self.uvnb_numpy()
        self._proj_matrix = P
        return P

    def grid_svg_path(self, nsamples=32):
        """ Return the SVG path for rendering a grid """
        P = self.proj_matrix()
        data = []
        for i in xrange(-2, 3):
            p0 = P * np.matrix([[i], [-2], [0], [1]])
            p1 = P * np.matrix([[i], [2], [0], [1]])
            p2 = P * np.matrix([[-2], [i], [0], [1]])
            p3 = P * np.matrix([[2], [i], [0], [1]])
            data.append("M%s %sL%s %sM%s %sL%s %s" % (
                p0[0, 0] / p0[3, 0], p0[1, 0] / p0[3, 0],
                p1[0, 0] / p1[3, 0], p1[1, 0] / p1[3, 0],
                p2[0, 0] / p2[3, 0], p2[1, 0] / p2[3, 0],
                p3[0, 0] / p3[3, 0], p3[1, 0] / p3[3, 0],
            ))
        return "".join(data)

    def disc_svg_path(self, nsamples=32):
        """ Return the SVG path for rendering the disc """
        P = self.proj_matrix()
        p = P * VEC4_X
        data = ["M%s %s" % (p[0, 0] / p[3, 0], p[1, 0] / p[3, 0])]
        for i in xrange(0, nsamples):
            p = P * np.matrix([
                [math.cos(2 * math.pi * i / nsamples)],
                [math.sin(2 * math.pi * i / nsamples)],
                [0],
                [1]
            ])
            data.append("L%s %s" % (
                p[0, 0] / p[3, 0], p[1, 0] / p[3, 0]
            ))
        data.append("z")
        return "".join(data)

    def pin_svg_path(self):
        """ Return the SVG path for rendering the pin """
        P = self.proj_matrix()
        n = P * VEC4_Z
        h0 = P * np.matrix([[0.2], [0], [0.8], [1]])
        h1 = P * np.matrix([[-0.2], [0], [0.8], [1]])
        h2 = P * np.matrix([[0], [0.2], [0.8], [1]])
        h3 = P * np.matrix([[0], [-0.2], [0.8], [1]])
        top = "%s %s" % (n[0, 0] / n[3, 0], n[1, 0] / n[3, 0])
        return "M%s %sL%sM%s %sL%sM%s %sL%sM%s %sL%sM%s %sL%s" % (
            P[0, 3] / P[3, 3], P[1, 3] / P[3, 3], top,
            h0[0, 0] / h0[3, 0], h0[1, 0] / h0[3, 0], top,
            h1[0, 0] / h1[3, 0], h1[1, 0] / h1[3, 0], top,
            h2[0, 0] / h2[3, 0], h2[1, 0] / h2[3, 0], top,
            h3[0, 0] / h3[3, 0], h3[1, 0] / h3[3, 0], top,
        )

    def axes_svg_path(self):
        """ Return the SVG path for rendering the two axes """
        P = self.proj_matrix()
        u = P * VEC4_X
        v = P * VEC4_Y
        px = P[0, 3] / P[3, 3]
        py = P[1, 3] / P[3, 3]
        return "M%s %sL%s %sM%s %sL%s %s" % (
            px, py, u[0, 0] / u[3, 0], u[1, 0] / u[3, 0],
            px, py, v[0, 0] / v[3, 0], v[1, 0] / v[3, 0],
        )

    def get_entry_dict(self):
        return {
            'id': self.id,
            'uvnb': self.uvnb,
            'shape': self.shape.get_entry_dict()
        }

    def orthogonalize(self, save=True):
        """ Adjusts the uvnb matrix to be orthogonal """
        m = self.uvnb_numpy()
        m[0:3, 0:3] = orthogonalize_matrix(m[0:3, 0:3])
        self.uvnb = json.dumps(list(m.flatten(order='F').flat))
        if save:
            self.save()

    def uvnb_numpy(self):
        """ Return the uvnb matrix as a numpy matrix """
        return np.matrix(json.loads(self.uvnb), dtype=float) \
            .reshape((4, 4), order='F')

    def save(self, *args, **kwargs):
        if not self.id:
            self.orthogonalize(save=False)
        if not self.image_rectified:
            from normals.utils import rectify_shape_from_uvnb
            img = rectify_shape_from_uvnb(self.shape, self)
            save_obj_attr_image(
                self, attr='image_rectified', img=img, save=False)

        super(ShapeRectifiedNormalLabel, self).save(*args, **kwargs)

    def better_than(self, other):
        """ Return ``True`` if ``self`` is a better surface normal than
        ``other``.  If the surface normal is determined by vanishing points, it
        is considered better.  Otherwise, the CUBAM score (``correct_score``)
        from quality voting is used. """

        if self is other:
            return False
        elif not other:
            return True
        elif bool(self.correct) != bool(other.correct):
            return self.correct
        elif self.automatic != other.automatic:
            return self.automatic
        else:
            return self.correct_score > other.correct_score

    #@classmethod
    #def mturk_needs_more(cls, instance):
        #""" Return True if more of this object should be scheduled """
        #correct_list = cls.objects \
            #.filter(shape=instance.shape) \
            #.values_list('correct', flat=True)
        ## only schedule more if all were graded and all were rejected
        #return (not correct_list) or all(c is False for c in correct_list)

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels or any(l.correct_score is None for l in labels):
            #return None
        #bad = sum(1 for l in labels if
                  #l.admin_score <= -2 or
                  #l.time_ms is None or
                  #l.time_active_ms < 2000 or
                  #(l.correct_score < -0.5 and l.time_ms < 60000))

        #if bad > 0 or any(l.correct_score < 0 for l in labels):
            #return float(bad) / float(len(labels))

        ## reward good rectifications
        #return sum(-1.0 for l in labels if
                   #l.correct and
                   #l.correct_score > 0.8 and
                   #l.time_active_ms > 20000)

    #@classmethod
    #def mturk_badness_reason(cls, mturk_assignment):
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if sum(1 for l in labels if abs(l.phi_degrees()) < 0.1):
            #return 'Z'
        #return None

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        new_objects = {}
        for shape in hit_contents:
            normal = results[unicode(shape.id)]
            shape_time_ms = time_ms[unicode(shape.id)]
            shape_time_active_ms = time_active_ms[unicode(shape.id)]

            new_obj, created = shape.rectified_normals.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=shape_time_ms,
                time_active_ms=shape_time_active_ms,
                uvnb=json.dumps(normal['uvnb']),
                method=normal['method'],
                focal_pixels=normal['focal_pixels'],
                canvas_width=normal['canvas_width'],
                canvas_height=normal['canvas_height'],
                pos_x=normal['pos_x'],
                pos_y=normal['pos_y'],
            )

            if created:
                new_objects[get_content_tuple(shape)] = [new_obj]

                # rectify synchronously (since this is a transaction and will
                # not be visible in another thread)
                from normals.tasks import auto_rectify_shape
                auto_rectify_shape(shape.id)

        return new_objects


class ShapeRectifiedNormalQuality(ResultBase):
    """ Vote on whether or not a rectified normal label matches """

    rectified_normal = models.ForeignKey(
        ShapeRectifiedNormalLabel, related_name='qualities')
    correct = models.BooleanField(default=False)
    canttell = models.NullBooleanField()

    def __unicode__(self):
        if self.canttell:
            return "can't tell"
        else:
            return 'correct' if self.correct else 'not correct'

    def get_thumb_template(self):
        return 'rectified_normal_label_thumb.html'

    class Meta:
        verbose_name = "Rectified normal quality vote"
        verbose_name_plural = "Rectified normal quality votes"

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #if any(l.rectified_normal.correct_score is None for l in labels):
            #return None
        #bad = sum(1 for l in labels if
                  #l.correct != l.rectified_normal.correct
                  #and abs(l.rectified_normal.correct_score) > 0.5)
        #return float(bad) / float(len(labels))

    #@classmethod
    #def mturk_badness_reason(cls, mturk_assignment):
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #T = sum(1 for l in labels if l.correct is True and l.correct is False)
        #F = sum(1 for l in labels if l.correct is False and l.correct is True)
        #if T > F * 1.25:
            #return 'T'
        #elif F > T * 1.25:
            #return 'F'
        #return None

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
        for rectified_normal in hit_contents:
            selected = (str(
                results[unicode(rectified_normal.id)]['selected']).lower()
                == 'true')
            canttell = (str(
                results[unicode(rectified_normal.id)]['canttell']).lower()
                == 'true')

            new_obj, created = ShapeRectifiedNormalQuality.objects.get_or_create(
                rectified_normal=rectified_normal,
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=avg_time_ms,
                time_active_ms=avg_time_active_ms,
                correct=selected,
                canttell=canttell,
            )

            if created:
                new_objects[get_content_tuple(rectified_normal)] = [new_obj]

        return new_objects
