import os
import json
import math
import tempfile
import numpy as np
from decimal import Decimal
from colormath.color_objects import RGBColor, LabColor

from django.db import models, transaction

from common.models import EmptyModelBase, ResultBase, PaperCitation
from photos.models import Photo

from common.utils import get_content_tuple, get_opensurfaces_storage


STORAGE = get_opensurfaces_storage()


class IntrinsicSyntheticDecomposition(EmptyModelBase):
    """
    This holds the different layers of a synthetic image.  The final rendered
    result is stored as an LDR JPG in the ``photo`` attribute, and the layers are
    stored in ``multilayer_exr``.  LDR preview thumbnails of each layer are
    stored in ``*_thumb``.
    """

    #: final rendered result as an LDR JPG.
    photo = models.OneToOneField(Photo, related_name='intrinsic_synthetic')

    #: name of the artist that modeled the scene
    scene_artist = models.CharField(max_length=255, blank=True)

    #: URL where the scene can be found online
    scene_url = models.URLField(max_length=255, blank=True)

    #: options for ``FileField`` or ``ImageField`` instance
    FILE_OPTS = {
        'null': True,
        'blank': True,
        'max_length': 255,
        'storage': STORAGE,
    }

    #: decomposition stored as a multi-layer EXR file
    multilayer_exr = models.FileField(upload_to='intrinsic_syn_multilayer_exr', **FILE_OPTS)

    #: md5 hash of the multilayer exr file
    md5 = models.CharField(max_length=32, unique=True)

    # decomposition separated out into thumbnail images for web visualization

    #: small LDR thumbnail of the environment lighting layer
    env_thumb = models.ImageField(upload_to='intrinsic_syn_env', **FILE_OPTS)

    #: small LDR thumbnail of the emitter layer
    emit_thumb = models.ImageField(upload_to='intrinsic_syn_emit', **FILE_OPTS)

    #: small LDR thumbnail of the depth layer
    depth_thumb = models.ImageField(upload_to='intrinsic_syn_depth', **FILE_OPTS)

    #: small LDR thumbnail of the normal layer
    normal_thumb = models.ImageField(upload_to='intrinsic_syn_normal', **FILE_OPTS)

    #: small LDR thumbnail of the diffuse color (albedo) layer
    diff_col_thumb = models.ImageField(upload_to='intrinsic_syn_diff_col', **FILE_OPTS)

    #: small LDR thumbnail of the diffuse indirect light layer
    diff_ind_thumb = models.ImageField(upload_to='intrinsic_syn_diff_ind', **FILE_OPTS)

    #: small LDR thumbnail of the diffuse direct light layer
    diff_dir_thumb = models.ImageField(upload_to='intrinsic_syn_diff_dir', **FILE_OPTS)

    #: small LDR thumbnail of the gloss color (albedo) layer
    gloss_col_thumb = models.ImageField(upload_to='intrinsic_syn_gloss_col', **FILE_OPTS)

    #: small LDR thumbnail of the gloss indirect light layer
    gloss_ind_thumb = models.ImageField(upload_to='intrinsic_syn_gloss_ind', **FILE_OPTS)

    #: small LDR thumbnail of the gloss direct light layer
    gloss_dir_thumb = models.ImageField(upload_to='intrinsic_syn_gloss_dir', **FILE_OPTS)

    #: small LDR thumbnail of the transparent color layer
    trans_col_thumb = models.ImageField(upload_to='intrinsic_syn_trans_col', **FILE_OPTS)

    #: small LDR thumbnail of the transparent indirect light layer
    trans_ind_thumb = models.ImageField(upload_to='intrinsic_syn_trans_ind', **FILE_OPTS)

    #: small LDR thumbnail of the transparent direct light layer
    trans_dir_thumb = models.ImageField(upload_to='intrinsic_syn_trans_dir', **FILE_OPTS)

    def _download_multilayer_exr(self, callback):
        """ Download the Multilayer EXR file, call a function, then delete it. """

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".exr")
        try:
            self.multilayer_exr.seek(0)
            temp.file.write(self.multilayer_exr.read())
            temp.file.close()
            return callback(temp.name)
        finally:
            os.remove(temp.name)

    def open_multilayer_exr(self, **kwargs):
        """ Open all layers from the decomposition as a dictionary
        See ``intrinsic.synthetic.open_multilayer_exr`` for list of arguments """

        # unfortunately the OpenEXR file insists on being givin a filename, so
        # we have to download the file to a temp directory
        from intrinsic.synthetic import open_multilayer_exr
        return self._download_multilayer_exr(
            lambda filename: open_multilayer_exr(filename, **kwargs))

    def open_multilayer_exr_layers(self, layers):
        """ Open a set of layers from the decomposition, returned as a numpy
        float array (linear space) """

        # unfortunately the OpenEXR file insists on being givin a filename, so
        # we have to download the file to a temp directory
        from intrinsic.synthetic import open_multilayer_exr_layers
        return self._download_multilayer_exr(
            lambda filename: open_multilayer_exr_layers(filename, layers))


class IntrinsicPoint(EmptyModelBase):

    """ A point where we want to say something about relative shading,
    reflectance, or both, with respect to another point. """

    #: photo of interest
    photo = models.ForeignKey(Photo, related_name='intrinsic_points')

    #: x and y are a fraction of width and height
    x = models.FloatField()
    #: x and y are a fraction of width and height
    y = models.FloatField()

    #: color at this point: "RRGGBB" in sRGB hex
    sRGB = models.CharField(max_length=6)

    #: synthetic ground truth diffuse albedo intensity (mean of reflectance
    #: color channels in the ``diff_col`` layer) at this point, if known.
    synthetic_diff_intensity = models.FloatField(blank=True, null=True)

    #: synthetic ground truth ``mean(diffuse contribution) / mean(combined pixel
    #: contribution)``, if known.  So, for fully diffuse points, this is 1.0, and
    #: for fully specular points, this is 0.0.
    synthetic_diff_fraction = models.FloatField(blank=True, null=True)

    #: synthetic ground truth ``std(diffuse contribution) / mean(diffuse
    #: contribution)``, if known, and if the mean is nonzero.
    synthetic_diff_cv = models.FloatField(blank=True, null=True)

    #: at what density was this point sampled (use decimals so we can compare
    #: these with exact equality).  This is converted to a distance in pixels
    #: according to ::
    #:
    #:     max(1, int(np.sqrt(cols ** 2 + rows ** 2) * min_separation))
    min_separation = models.DecimalField(
        default=Decimal('0.07'), decimal_places=5, max_digits=7)

    #: if True: enough users voted this to be ``opaque`` (not a mirror and not
    #: transparent).
    #: if None: not yet known.
    opaque = models.NullBooleanField()

    #: CUBAM score for the ``opaque`` field.
    #: higher scores indicate higher probability of being opaque.
    #: scores are thresholded at 0.
    opaque_score = models.FloatField(blank=True, null=True, db_index=True)

    #: method used to set the opaque field (admin, CUBAM, or majority vote)
    opaque_method = models.CharField(
        max_length=1, choices=ResultBase.QUALITY_METHODS, blank=True, null=True)

    def get_rgb(self):
        """ return the color as a list """
        if not hasattr(self, '_rgb'):
            c = RGBColor()
            c.set_from_rgb_hex(self.sRGB)
            self._rgb = (c.rgb_r / 255.0, c.rgb_g / 255.0, c.rgb_b / 255.0)
        return self._rgb

    def get_intensity(self):
        """ returns mean(rgb) """
        return np.mean(self.get_rgb())

    def get_lab(self):
        """ returns the current point in L*a*b* """
        if not hasattr(self, '_lab'):
            c = RGBColor()
            c.set_from_rgb_hex(self.sRGB)
            self._lab = c.convert_to('lab').get_value_tuple()
        return self._lab

    def get_chroma(self):
        """ returns rgb / sum(rgb).  pure black has the same chromaticity as pure white. """
        rgb = self.get_rgb()
        s = np.sum(rgb)
        if s > 0:
            return np.asarray(rgb) / s
        else:
            return np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])

    def save(self, *args, **kwargs):
        if not self.sRGB:
            rgb = self.photo.get_pixel(self.x, self.y, width='300')
            self.sRGB = '%02x%02x%02x' % rgb

        super(IntrinsicPoint, self).save(*args, **kwargs)

    def update_opacity(self, save=True):
        """ Update the opaque field by aggregating user responses and selecting
        the majority vote.  Note that the opaque field is updated periodically
        with the output of CUBAM, which is a better predictor than majority
        vote.  """
        opacities = self.opacities.filter(invalid=False) \
            .values_list('opaque', flat=True)
        if (len(opacities) >= 5 and
                (not self.opaque_method or self.opaque_method == 'M')):
            # If 100% in agreement, store in advance.  Otherwise,
            # wait for CUBAM to assign the answer.
            num_opaque = sum(int(b) for b in opacities)
            if num_opaque == 0 or num_opaque == len(opacities):
                self.opaque = (num_opaque * 2 > len(opacities))
                self.opaque_score = None
                self.opaque_method = 'M'
                if save:
                    self.save()

    def x_aspect(self):
        """ Helper for templates.  Return the x pixel coordinate, scaled by
        height instead of width (i.e. x_aspect = x_original / height) """
        return self.x * self.photo.aspect_ratio

    def get_entry_dict(self, include_photo=True):
        """ Return a dictionary of this model containing just the fields needed
        for javascript rendering.  """
        ret = {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'sRGB': self.sRGB,
        }
        if include_photo:
            ret['photo'] = self.photo.get_entry_dict()
        return ret


class IntrinsicPointOpacityResponse(ResultBase):

    """ A user's opinion of a point's opacity.  Note that "opaque" additionally
    excludes pure mirrors.  In BRDF terms, opaque points have only diffuse or
    glossy reflection components, and no transmission component. """

    #: point being classified
    point = models.ForeignKey(IntrinsicPoint, related_name='opacities')

    #: if True: not a mirror and not transparent.
    #: if False: either a mirror or transparent.
    opaque = models.BooleanField(default=False)

    #: The zoom level that the user used in the UI when deciding on opaque
    #: (1: zoomed out, larger numbers indicate zoomed in further.
    zoom = models.FloatField(null=True, blank=True)

    #: List of all ForeignKey relationships that are accessed during a mturk
    #: task.  (called by mturk.utils.get_content_model_prefetch)
    MTURK_PREFETCH = ('point', 'point__photo')

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms,
                     time_active_ms, version,
                     mturk_assignment=None, **kwargs):

        if unicode(version) != u'1.0':
            raise ValueError(
                "Unknown version: '%s' (type: %s)" % (version, type(version)))

        new_objects = {}
        for point in hit_contents:
            key = unicode(point.id)

            new_obj, created = point.opacities.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=time_ms[key],
                time_active_ms=time_active_ms[key],
                opaque=results[key][u'opaque'],
                zoom=results[key][u'zoom'],
            )

            if created:
                new_objects[get_content_tuple(point)] = [new_obj]

        # atomically update comparison objects
        with transaction.atomic():
            qset = IntrinsicPoint.objects \
                .select_for_update() \
                .filter(id__in=[c.id for c in hit_contents])
            for point in qset:
                point.update_opacity()

        return new_objects

    @staticmethod
    def get_thumb_template():
        return 'intrinsic/point_opacity_thumb.html'

    def expanded_bbox(self):
        if not hasattr(self, '_expanded_bbox'):
            x1, y1 = self.point1.x * self.photo.aspect_ratio, self.point1.y
            x2, y2 = self.point2.x * self.photo.aspect_ratio, self.point2.y
            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1
            self._expanded_bbox = [x1 - 0.1, x2 + 0.1, y1 - 0.1, y2 + 0.1]
        return self._expanded_bbox

    def view_box_svg(self):
        x = self.point.x_aspect()
        y = self.point.y
        return "%s %s 0.1 0.1" % (x - 0.05, y - 0.05)


class IntrinsicPointComparison(EmptyModelBase):

    """ Pair of points where we want to say something about their relative
    reflectance.  The user must explain which point has a darker reflectance.
    To maintain unique ordering of points, point1 and point2 must be ordered
    so that:

    .. code-block:: py

        point1.y < point2.y if point1.x == point2.x
        point1.x < point2.x if point1.x != point2.x

    """

    #: photo of interest
    photo = models.ForeignKey(
        Photo, related_name='intrinsic_comparisons')

    #: first point in the comparison.
    #: note: point1 and point2 must be from the same photo
    point1 = models.ForeignKey(
        IntrinsicPoint, related_name='comparison_point1')

    #: second point in the comparison.
    #: note: point1 and point2 must be from the same photo
    point2 = models.ForeignKey(
        IntrinsicPoint, related_name='comparison_point2')

    #: ``True`` if the luminance of the RGB pixel value at ``point1`` is darker
    #: than that of ``point2``
    point1_image_darker = models.NullBooleanField()

    #: darker: which point is darker
    DARKER_CHOICES = (('1', '1 < 2'), ('2', '1 > 1'), ('E', '1 = 2'))
    darker_to_str = dict((k, v) for (k, v) in DARKER_CHOICES)
    darker = models.CharField(
        max_length=1, choices=DARKER_CHOICES,
        blank=True, null=True)

    #: if synthetic, the ratio (point1/point2) of the intensity of the
    #: ``diff_col`` channel (diffuse albedo) of the multilayer exr rendering.
    #: If the ground truth intensity is 0, then this is not computed.
    synthetic_diff_intensity_ratio = models.FloatField(blank=True, null=True)

    #: CUBAM score for final decision
    darker_score = models.FloatField(blank=True, null=True)

    #: method used to set the ``darker`` field (admin, CUBAM, or majority vote)
    darker_method = models.CharField(
        max_length=1, choices=ResultBase.QUALITY_METHODS, blank=True, null=True)

    #: This is equal to ``darker == "E"``.  This is used for aggregating votes
    #: with CUBAM.
    reflectance_eq = models.NullBooleanField()

    #: CUBAM score for ``reflectance_eq``
    reflectance_eq_score = models.FloatField(blank=True, null=True)

    #: boolean version of the answer: if ``True``, the darker pixel
    #: has a darker reflectance
    reflectance_dd = models.NullBooleanField()

    #: CUBAM score for ``reflectance_dd``
    reflectance_dd_score = models.FloatField(blank=True, null=True)

    #: List of all ForeignKey relationships that are accessed during a mturk
    #: task.  (called by mturk.utils.get_content_model_prefetch)
    MTURK_PREFETCH = ('photo', 'point1', 'point2')

    class Meta:
        ordering = ['photo', '-darker_score']
        unique_together = (("point1", "point2"))

    def __unicode__(self):
        if self.darker:
            return self.darker_to_str[self.darker]
        else:
            return 'Unknown'

    def expanded_bbox(self):
        if not hasattr(self, '_expanded_bbox'):
            x1, y1 = self.point1.x * self.photo.aspect_ratio, self.point1.y
            x2, y2 = self.point2.x * self.photo.aspect_ratio, self.point2.y
            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1
            self._expanded_bbox = [x1 - 0.1, x2 + 0.1, y1 - 0.1, y2 + 0.1]
        return self._expanded_bbox

    def view_box_svg(self):
        bb = self.expanded_bbox()
        return "%s %s %s %s" % (bb[0], bb[2], bb[1] - bb[0], bb[3] - bb[2])

    def view_box_aspect(self):
        bb = self.expanded_bbox()
        return (bb[1] - bb[0]) / (bb[3] - bb[2])

    def save(self, *args, **kwargs):
        if (self.point1.photo_id != self.photo_id or
                self.point2.photo_id != self.photo_id):
            raise ValueError("Photo mismatch: %s %s %s" % (
                self.photo_id, self.point1.photo_id, self.point2.photo_id))
        if self.point1_image_darker is None:
            self.point1_image_darker = (
                self.point1.get_lab()[0] < self.point2.get_lab()[0])
        super(IntrinsicPointComparison, self).save(*args, **kwargs)

    def get_entry_dict(self):
        """ Return a dictionary of this model containing just the fields needed
        for javascript rendering.  """
        return {
            'id': self.id,
            'photo': self.photo.get_entry_dict(),
            'point1': self.point1.get_entry_dict(include_photo=False),
            'point2': self.point2.get_entry_dict(include_photo=False),
        }

    def svg_path(self, radius=0.015):
        """ Return the svg path attribute """
        p1 = np.array([self.point1.x * self.photo.aspect_ratio, self.point1.y])
        p2 = np.array([self.point2.x * self.photo.aspect_ratio, self.point2.y])
        if self.darker == '1':
            p1, p2 = p2, p1
        v = p2 - p1
        v *= radius / np.linalg.norm(v)
        p = np.array([-v[1], v[0]])
        if not self.darker:
            return 'M %s %s L %s %s' % (
                p1[0] + v[0], p1[1] + v[1],
                p2[0] - v[0], p2[1] - v[1],
            )
        if self.darker == 'E':
            p /= 4
            return 'M %s %s L %s %s L %s %s L %s %s z' % (
                p1[0] - p[0] + v[0], p1[1] - p[1] + v[1],
                p1[0] + p[0] + v[0], p1[1] + p[1] + v[1],
                p2[0] + p[0] - v[0], p2[1] + p[1] - v[1],
                p2[0] - p[0] - v[0], p2[1] - p[1] - v[1],
            )
        elif self.darker in ['1', '2']:
            angle = math.degrees(math.atan2(v[1], v[0]))
            return 'M %s %s A %s %s %s %s %s %s %s L %s %s z' % (
                p1[0] - p[0], p1[1] - p[1],
                radius, radius, angle, 1, 1,
                p1[0] + p[0], p1[1] + p[1],
                p2[0] - v[0], p2[1] - v[1],
            )
        else:
            return ''

    def svg_style(self):
        """ Return the svg style attribute """
        if self.darker:
            if self.darker_method == 'A':
                return 'fill: #49D36A'
            else:
                t = np.clip(abs(self.darker_score), 0, 1)
                lab0 = np.array([40, 30, -70])
                lab1 = np.array([70, 30, 70])
                lab = t * lab0 + (1 - t) * lab1
                rgb = np.clip(LabColor(*lab).convert_to('rgb').get_value_tuple(), 0, 255)
                return 'fill: #%02x%02x%02x' % tuple(rgb.astype(int))
        else:
            return ""

    def synthetic_darker(self, thresh=0.05):
        """ Return the expected/true judgement for a given threshold """

        # synthetic_diff_intensity_ratio: point1/point2
        if self.synthetic_diff_intensity_ratio is None:
            return None
        ratio = max(self.synthetic_diff_intensity_ratio, 1e-10)
        if ratio > 1.0 + thresh:
            return "2"
        elif (1.0 / ratio) > 1.0 + thresh:
            return "1"
        else:
            return "E"

    def darker_score_perc(self):
        """ Return the darker score as an int percentage """
        return int(self.darker_score * 100)

    @staticmethod
    def get_thumb_template():
        """ Return the template path for rendering thumbnails """
        return 'intrinsic/comparison_thumb.html'

    def comparison(self):
        """ Return ``self`` (helper for templates) """
        return self


class IntrinsicPointComparisonResponse(ResultBase):

    """ A user's answer to the comparison """

    comparison = models.ForeignKey(
        IntrinsicPointComparison, related_name='responses')

    #: '1': 1 is darker
    #: '2': 2 is darker
    #: 'E': the points are equal
    darker = models.CharField(
        max_length=1, choices=IntrinsicPointComparison.DARKER_CHOICES)

    #: 0: guessing, 1: probably, 2: definitely
    confidence = models.IntegerField()

    #: boolean version of the answer: stores whether ``darker == "E"``.  This
    #: is used for aggregating votes with CUBAM.
    reflectance_eq = models.BooleanField(default=False)

    #: boolean version of the answer: if ``True``, the darker pixel
    #: has a darker reflectance
    reflectance_dd = models.NullBooleanField()

    def __unicode__(self):
        if self.darker:
            return IntrinsicPointComparison.darker_to_str[self.darker]
        else:
            return 'Unknown'

    @staticmethod
    def mturk_grade_test(test_content_wrappers, test_contents, results):
        responses = [
            results[unicode(comparison.id)]['darker']
            for comparison in test_contents
        ]
        # Note that if darker_method != 'A' (set by admin), then CUBAM can
        # change it, so we just give it to them for free
        responses_correct = [
            (not comparison.darker or comparison.darker_method != 'A' or
             bool(unicode(responses[i]) == unicode(comparison.darker)))
            for i, comparison in enumerate(test_contents)
        ]
        return responses, responses_correct

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):

        if unicode(version) != u'1.0':
            raise ValueError(
                "Unknown version: '%s' (type: %s)" % (version, type(version)))

        new_objects = {}
        for comparison in hit_contents:
            key = unicode(comparison.id)
            darker = results[key][u'darker']
            confidence = results[key][u'confidence']

            reflectance_dd = None
            if darker == "E":
                reflectance_eq = True
            else:
                reflectance_eq = False
                if comparison.point1_image_darker is not None:
                    if darker == "1":
                        reflectance_dd = comparison.point1_image_darker
                    elif darker == "2":
                        reflectance_dd = not comparison.point1_image_darker

            new_obj, created = comparison.responses.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=time_ms[key],
                time_active_ms=time_active_ms[key],
                darker=darker,
                confidence=confidence,
                reflectance_eq=reflectance_eq,
                reflectance_dd=reflectance_dd,
            )

            if created:
                new_objects[get_content_tuple(comparison)] = [new_obj]

        # clear any existing aggregation
        IntrinsicPointComparison.objects \
            .filter(id__in=[c.id for c in hit_contents]) \
            .update(darker=None, darker_score=None,
                    reflectance_dd=None, reflectance_dd_score=None,
                    reflectance_eq=None, reflectance_eq_score=None)

        return new_objects

    @staticmethod
    def get_thumb_template():
        return 'intrinsic/comparison_response_thumb.html'


class IntrinsicImagesAlgorithm(EmptyModelBase):
    """ An algorithm together with the parameters used """

    #: url-friendly name of the algorithm
    slug = models.CharField(max_length=128)

    #: citation for this algorithm
    citation = models.ForeignKey(PaperCitation, blank=True, null=True)

    #: json-encoded dictionary of the parameters used
    parameters = models.TextField(blank=True)

    #: if ``True``, this algorithm is a simple non-algorithm
    baseline = models.BooleanField(default=False)

    #: if ``True``, this is part of the current set of comparisons
    active = models.BooleanField(default=True)

    #: counter to keep track of stale jobs; this is only used during scheduling
    #: of decompositions.  Increment this number to invalidate current tasks.
    task_version = models.IntegerField(default=0)

    #: mean error across all IIW ("Intrinsic Images in the Wild" paper) images
    iiw_mean_error = models.FloatField(blank=True, null=True)

    #: mean runtime across all IIW ("Intrinsic Images in the Wild" paper) images
    iiw_mean_runtime = models.FloatField(blank=True, null=True)

    #: is this the best parameter setting for this slug?
    iiw_best = models.BooleanField(default=False)

    def iiw_mean_error_pretty(self):
        return '%.1f%%' % (100.0 * self.iiw_mean_error)

    def parameters_pretty_html(self):
        """ Render the parameters as HTML """

        params = json.loads(self.parameters)
        if not params:
            return "None"
        ret = []
        for p, v in params.iteritems():
            #if p == "remap_gamma_2_2":
                #continue
            if isinstance(v, (float, int, long)):
                for exp in xrange(2, 20):
                    if abs(v - 10 ** exp) < 1e-6:
                        v = "10<sup>%s</sup>" % exp
                        break
                else:
                    if isinstance(v, float):
                        v = round(v, max(0, 2 + int(-math.log10(v))))
            ret.append("%s: %s" % (p.replace('_', ' '), v))
        return "<ul><li>%s</ul>" % "<li>".join(sorted(ret))

    def save(self, *args, **kwargs):
        # make sure that json-formatted string is sorted by keys
        if self.parameters:
            self.parameters = json.dumps(
                json.loads(self.parameters), sort_keys=True)
        super(IntrinsicImagesAlgorithm, self).save(*args, **kwargs)

    class Meta:
        unique_together = (('slug', 'parameters'))


class IntrinsicImagesDecomposition(EmptyModelBase):
    """ Result of running an intrinisc images algorithm """

    #: input photograph
    photo = models.ForeignKey(
        Photo, related_name='intrinsic_images_decompositions')

    #: algorithm used
    algorithm = models.ForeignKey(
        IntrinsicImagesAlgorithm, related_name='intrinsic_images_decompositions')

    #: time taken to run in seconds
    runtime = models.FloatField(blank=True, null=True)

    #: algorithm output
    reflectance_image = models.ImageField(
        upload_to='intrinsic_reflectance',
        null=True, blank=True, max_length=255,
        storage=STORAGE,
    )

    #: recomputed shading image from the algorithm output
    shading_image = models.ImageField(
        upload_to='intrinsic_shading',
        null=True, blank=True, max_length=255,
        storage=STORAGE,
    )

    def reset_error(self, save=True):
        for attr in IntrinsicImagesDecomposition.ERROR_ATTRS:
            setattr(self, attr, None)
        self.error_comparison_thresh = None
        if save:
            self.save()

    def mean_error_pretty(self):
        return '%.1f%%' % (100.0 * self.mean_error)

    #: attributes on this instance corresponding to an error measure
    ERROR_ATTRS = [
        'mean_dense_error', 'mean_sparse_error', 'mean_error',
        'mean_eq_error', 'mean_neq_error', 'mean_sum_error',
    ]

    #: error of this across all comparisons
    mean_error = models.FloatField(blank=True, null=True)

    #: error of this across all dense comparisons
    mean_dense_error = models.FloatField(blank=True, null=True)

    #: error of this across all sparse comparisons
    mean_sparse_error = models.FloatField(blank=True, null=True)

    #: error of this decomposition from equality
    mean_eq_error = models.FloatField(blank=True, null=True)

    #: error of this decomposition from inequality
    mean_neq_error = models.FloatField(blank=True, null=True)

    #: sum of error types
    mean_sum_error = models.FloatField(blank=True, null=True)

    #: number of comparisons used in evaluating all errors
    num = models.IntegerField(blank=True, null=True)

    #: number of comparisons used in evaluating the dense error
    num_dense = models.IntegerField(blank=True, null=True)

    #: number of comparisons used in evaluating the dense error
    num_sparse = models.IntegerField(blank=True, null=True)

    #: number of comparisons used in evaluating the equality error
    num_eq = models.IntegerField(blank=True, null=True)

    #: number of comparisons used in evaluating the inequality error
    num_neq = models.IntegerField(blank=True, null=True)

    #: threshold used in the comparison error metric
    error_comparison_thresh = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = (('photo', 'algorithm'))
        ordering = ['mean_error', '-id']
        #ordering = ['-id']
