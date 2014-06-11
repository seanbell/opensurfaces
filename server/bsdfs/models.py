import math
import json

from colormath.color_objects import RGBColor

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from common.models import UserBase, ResultBase
from common.utils import save_obj_attr_base64_image, get_content_tuple, \
    get_opensurfaces_storage

from shapes.models import Shape, MaterialShape, MaterialShapeLabelBase


BSDF_VERSIONS = ("wd", ) # just Ward for now
STORAGE = get_opensurfaces_storage()


class EnvironmentMap(UserBase):
    """ Environment map used with a BRDF """
    name = models.CharField(max_length=128, unique=True)

    # Tonemapping parameters for [Reinhard 2002, Equation 4]
    # The log_average luminance is baked into the scale as a
    # precomputation.
    #     scale: key / log_average luminance
    #     white: values higher than this will be set to pure white
    tonemap_scale = models.FloatField()
    tonemap_white = models.FloatField()


class ShapeBsdfLabelBase(MaterialShapeLabelBase):
    """ Base class of BSDF labels"""

    # json-encoded dictionary of counts (where each count is the number of
    # times a UI element was adjusted)
    edit_dict = models.TextField(blank=True)
    # sum of the values in edit_dict
    edit_sum = models.IntegerField(default=0)
    # number of nonzero values in edit_dict
    edit_nnz = models.IntegerField(default=0)

    # environment map used to light the blob
    envmap = models.ForeignKey(EnvironmentMap, null=True, blank=True)

    # screenshot
    image_blob = models.ImageField(
        upload_to='blobs', null=True, blank=True, max_length=255,
        storage=STORAGE)

    # option to give up
    give_up = models.BooleanField(default=False)
    give_up_msg = models.TextField(blank=True)

    # reverse generic relationship for quality votes
    qualities = generic.GenericRelation(
        'ShapeBsdfQuality', content_type_field='content_type',
        object_id_field='object_id')

    # first voting stage: color matches?
    color_correct = models.NullBooleanField()
    # further from 0: more confident in assignment of color_correct
    color_correct_score = models.FloatField(null=True, blank=True)

    # second voting stage: gloss matches?
    gloss_correct = models.NullBooleanField()
    # further from 0: more confident in assignment of gloss_correct
    gloss_correct_score = models.FloatField(null=True, blank=True)

    # The method by which the reflectance widget was initialized
    INIT_METHODS = (
        ('KM', 'k-means color, middle value gloss'),
        ('KR', 'k-means color, random gloss')
    )
    init_method_to_str = dict((k, v) for (k, v) in INIT_METHODS)
    init_method = models.CharField(max_length=2, choices=INIT_METHODS)

    # L*a*b* colorspace for matching blobs
    color_L = models.FloatField(blank=True, null=True)
    color_a = models.FloatField(blank=True, null=True)
    color_b = models.FloatField(blank=True, null=True)

    def better_than(self, other):
        if self is other:
            return False
        elif not other:
            return True
        elif self.invalid != other.invalid:
            return not self.invalid
        elif bool(self.color_correct) != bool(other.color_correct):
            return bool(self.color_correct)
        elif bool(self.gloss_correct) != bool(other.gloss_correct):
            return bool(self.gloss_correct)
        else:
            try:
                return (self.color_correct_score + self.gloss_correct_score >
                        other.color_correct_score + other.gloss_correct_score)
            except TypeError:
                return True

    def get_entry_dict(self):
        return {'id': self.id, 'shape': self.shape.get_entry_dict()}

    def mark_invalid(self, *args, **kwargs):
        self.color_correct = False
        self.gloss_correct = False
        super(Shape, self).mark_invalid(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['-edit_nnz', '-time_ms']

    #@classmethod
    #def mturk_needs_more(cls, instance):
        #""" Return True if more of this object should be scheduled """
        #correct_list = cls.objects \
            #.filter(shape=instance.shape) \
            #.values_list('color_correct', 'gloss_correct')
        ## only schedule more if all were graded and all were rejected
        #return ((not correct_list) or
                #all((c[0] is False or c[1] is False) for c in correct_list))

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """

        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if (not labels or any((l.color_correct_score is None and
                               #l.gloss_correct_score is None) for l in labels)):
            #return None

        #bad = sum(1 for l in labels if
                  #l.admin_score <= -2 or
                  #l.time_ms is None or
                  #l.edit_nnz <= 1 or
                  #(l.color_correct_score is not None and
                   #l.color_correct_score < -0.5 and l.time_ms < 60000) or
                  #(l.gloss_correct_score is not None and
                   #l.gloss_correct_score < -0.5 and l.time_ms < 60000))

        #if bad > 0 or any(l.color_correct_score < 0 or l.gloss_correct_score < 0 for l in labels):
            #return float(bad) / float(len(labels))

        ## reward good rectifications
        #return sum(-1.0 for l in labels if
                   #l.color_correct_score > 0.5 and
                   #l.gloss_correct_score > 0.5 and
                   #l.time_ms > 10000)


class ShapeBsdfLabel_mf(ShapeBsdfLabelBase):
    """
    Microfacet BSDF model
    ** CURRENTLY UNUSED **
    """

    shape = models.ForeignKey(MaterialShape, related_name='bsdfs_mf')

    BSDF_TYPES = (('P', 'plastic'), ('C', 'conductor'))
    bsdf_type_to_str = {k: v for k, v in BSDF_TYPES}
    str_to_bsdf_type = {v: k for k, v in BSDF_TYPES}

    # plastic or conductor
    bsdf_type = models.CharField(max_length=1, choices=BSDF_TYPES)
    alpha_index = models.IntegerField()   # integer index into roughness table
    specular = models.FloatField()        # specular weight
    color_sRGB = models.CharField(max_length=6)  # "RRGGBB" hex

    def type_name(self):
        return ShapeBsdfLabel_mf.bsdf_type_to_str[self.bsdf_type]

    @staticmethod
    def version():
        return 'mf'

    def __unicode__(self):
        return '%s alpha_index=%s color=%s' % (
            self.bsdf_type, self.alpha, self.color)

    def get_thumb_template(self):
        return 'bsdf_mf_shape_thumb.html'

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        raise NotImplementedError("TODO")


class ShapeBsdfLabel_wd(ShapeBsdfLabelBase):
    """
    Ward BSDF model.

    Note: This is the "balanced" ward-duel model with energy balance at all angles
    from [Geisler-Moroder, D., and Dur, A. A new ward brdf model with bounded
    albedo. In Computer Graphics Forum (2010), vol. 29, Wiley Online Library,
    pp. 1391-1398.].  We use the implementation from Mitsuba available at
    http://www.mitsuba-renderer.org.
    """

    shape = models.ForeignKey(MaterialShape, related_name='bsdfs_wd')

    # c in [0, 1]
    contrast = models.FloatField()

    # d in [0, 15] discretized alpha
    doi = models.IntegerField()

    # true if the 'rho_s only' was selected, false if traditional ward
    metallic = models.BooleanField(default=False)

    # color in "#RRGGBB" sRGB hex format
    color = models.CharField(max_length=7)

    @staticmethod
    def version():
        return 'wd'

    def __unicode__(self):
        return 'ward sRGB=%s' % (self.color)

    def get_thumb_template(self):
        return 'bsdf_wd_shape_thumb.html'

    def c(self):
        return self.contrast

    def d(self):
        return 1 - (0.001 + (15 - self.doi) * 0.2 / 15)

    def d_edits(self):
        return json.loads(self.edit_dict)['doi']

    def c_edits(self):
        return json.loads(self.edit_dict)['contrast']

    def alpha(self):
        return 1 - self.d()

    def rho_s(self):
        rho_s = self.rho()[1]
        return '%0.3f, %0.3f, %0.3f' % rho_s

    def rho_d(self):
        rho_d = self.rho()[0]
        return '%0.3f, %0.3f, %0.3f' % rho_d

    def rho(self):
        if not hasattr(self, '_rho'):
            rgb = self.colormath_rgb()
            v = self.v()
            # approximate cielab_inverse_f.
            # we have V instead of L, so the same inverse formula doesn't
            # apply anyway.
            finv = v ** 3
            if self.metallic:
                rho_s = finv
                s = rho_s / (v * 255.0) if v > 0 else 0
                self._rho = (
                    (0, 0, 0),
                    (s * rgb.rgb_r, s * rgb.rgb_g, s * rgb.rgb_b),
                )
            else:
                rho_d = finv
                t = self.contrast + (rho_d * 0.5) ** (1.0 / 3.0)
                rho_s = t ** 3 - rho_d * 0.5
                rho_t = rho_s + rho_d
                if rho_t > 1:
                    rho_s /= rho_t
                    rho_d /= rho_t
                s = rho_d / (v * 255.0) if v > 0 else 0
                self._rho = (
                    (s * rgb.rgb_r, s * rgb.rgb_g, s * rgb.rgb_b),
                    (rho_s, rho_s, rho_s)
                )
        return self._rho

    def v(self):
        """ Return the V component of HSV, in the range [0, 1] """
        rgb = self.colormath_rgb()
        return max(rgb.rgb_r, rgb.rgb_b, rgb.rgb_g) / 255.0

    def colormath_rgb(self):
        if not hasattr(self, '_colormath_rgb'):
            self._colormath_rgb = RGBColor()
            self._colormath_rgb.set_from_rgb_hex(self.color)
        return self._colormath_rgb

    def colormath_lab(self):
        if not hasattr(self, '_colormath_lab'):
            self._colormath_lab = self.colormath_rgb().convert_to('lab')
        return self._colormath_lab

    def color_distance(self, bsdf):
        return math.sqrt((self.color_L - bsdf.color_L) ** 2 +
                         (self.color_a - bsdf.color_a) ** 2 +
                         (self.color_b - bsdf.color_b) ** 2)

    def gloss_distance(self, bsdf):
        return math.sqrt((self.c() - bsdf.c()) ** 2 +
                        (1.78 * (self.d() - bsdf.d())) ** 2)

    def save(self, *args, **kwargs):
        if (self.color_L is None) or (self.color_a is None) or (self.color_b is None):
            c = RGBColor()
            c.set_from_rgb_hex(self.color)
            c = c.convert_to('lab')
            self.color_L = c.lab_l
            self.color_a = c.lab_a
            self.color_b = c.lab_b
        super(ShapeBsdfLabel_wd, self).save(*args, **kwargs)

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     experiment, mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        new_objects = {}
        for shape in hit_contents:
            d = results[unicode(shape.id)]
            shape_time_ms = time_ms[unicode(shape.id)]
            shape_time_active_ms = time_active_ms[unicode(shape.id)]

            edit_dict = d[u'edit']
            edit_sum = sum(int(edit_dict[k]) for k in edit_dict)
            edit_nnz = sum(int(int(edit_dict[k]) > 0) for k in edit_dict)

            init_method = 'KR'
            envmap = EnvironmentMap.objects.get(
                id=json.loads(experiment.variant)['envmap_id'])

            doi = int(d[u'doi'])
            contrast = float(d[u'contrast'])
            metallic = (int(d[u'type']) == 1)
            color = d['color']

            give_up = d[u'give_up']
            give_up_msg = d[u'give_up_msg']

            bsdf, bsdf_created = shape.bsdfs_wd.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=shape_time_ms,
                time_active_ms=shape_time_active_ms,
                doi=doi,
                contrast=contrast,
                metallic=metallic,
                color=color,
                give_up=give_up,
                give_up_msg=give_up_msg,
                edit_dict=json.dumps(edit_dict),
                edit_sum=edit_sum,
                edit_nnz=edit_nnz,
                envmap=envmap,
                init_method=init_method,
            )

            if bsdf_created:
                new_objects[get_content_tuple(shape)] = [bsdf]

            if ((not bsdf.image_blob) and 'screenshot' in d and d['screenshot'].startswith('data:image/')):
                save_obj_attr_base64_image(bsdf, 'image_blob', d['screenshot'])

        return new_objects


class ShapeBsdfQuality(ResultBase):
    """ Vote on whether or not a BSDF matches its shape.  The foreign key to
    the BSDF is generic since there are multiple BSDF models. """

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    bsdf = generic.GenericForeignKey('content_type', 'object_id')

    color_correct = models.NullBooleanField()
    gloss_correct = models.NullBooleanField()
    canttell = models.NullBooleanField()

    def __unicode__(self):
        if self.canttell:
            return "can't tell"
        else:
            if self.has_color():
                if self.has_gloss():
                    return 'gloss: %s, color: %s' % (
                        self.gloss_correct, self.color_correct,
                    )
                return 'color: %s' % self.color_correct
            elif self.has_gloss:
                return 'gloss: %s' % self.gloss_correct
            else:
                return 'INVALID LABEL'

    def get_thumb_template(self):
        return 'bsdf_%s_shape_label_thumb.html' % (
            self.content_type.model_class().version())

    def has_color(self):
        return self.color_correct is not None

    def has_gloss(self):
        return self.gloss_correct is not None

    class Meta:
        verbose_name = "BSDF quality vote"
        verbose_name_plural = "BSDF quality votes"

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #if any((l.color_correct is not None and
                #l.bsdf.color_correct_score is None) or
               #(l.gloss_correct is not None and
                #l.bsdf.gloss_correct_score is None)
               #for l in labels):
            #return None
        #bad = sum(1 for l in labels if
                  #(l.color_correct is not None and
                   #l.color_correct != l.bsdf.color_correct and
                   #abs(l.bsdf.color_correct_score) > 0.5) or
                  #(l.gloss_correct is not None and
                   #l.gloss_correct != l.bsdf.gloss_correct and
                   #abs(l.bsdf.color_correct_score) > 0.5))
        #return float(bad) / float(len(labels))

    #@classmethod
    #def mturk_badness_reason(cls, mturk_assignment):
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #T = sum(1 for l in labels if
                #(l.color_correct is True and l.bsdf.color_correct is False) or
                #(l.gloss_correct is True and l.bsdf.gloss_correct is False))
        #F = sum(1 for l in labels if
                #(l.color_correct is False and l.bsdf.color_correct is True) or
                #(l.gloss_correct is False and l.bsdf.gloss_correct is True))
        #if T > F * 1.5:
            #return 'T'
        #elif F > T * 1.5:
            #return 'F'
        #return None

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     experiment, mturk_assignment=None, **kwargs):
        """ Add new instances from a mturk HIT after the user clicks [submit] """

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        # best we can do is average
        avg_time_ms = time_ms / len(hit_contents)
        avg_time_active_ms = time_active_ms / len(hit_contents)

        new_objects = {}
        for bsdf in hit_contents:
            selected = (str(results[unicode(bsdf.id)]['selected']).lower()
                        == 'true')
            canttell = (str(results[unicode(bsdf.id)]['canttell']).lower()
                        == 'true')

            color_correct = None
            gloss_correct = None
            if 'color' in experiment.slug:
                color_correct = selected
            elif 'gloss' in experiment.slug:
                gloss_correct = selected

            content_tuple = get_content_tuple(bsdf)
            new_obj, created = ShapeBsdfQuality.objects.get_or_create(
                content_type=ContentType.objects.get_for_id(content_tuple[0]),
                object_id=content_tuple[1],
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=avg_time_ms,
                time_active_ms=avg_time_active_ms,
                color_correct=color_correct,
                gloss_correct=gloss_correct,
                canttell=canttell
            )

            if created:
                new_objects[content_tuple] = [new_obj]

        return new_objects
