import math
import json

from colormath.color_objects import RGBColor

from django.db import models
from django.core.urlresolvers import reverse

from imagekit.models import ImageSpecField
from imagekit.processors import SmartResize, ResizeToFit
from imagekit.utils import open_image

from common.models import UserBase, ResultBase, EmptyModelBase
from licenses.models import License

from common.utils import compute_label_reward, md5sum, get_content_tuple, \
    get_opensurfaces_storage
from common.geom import normalized, construct_all_uvn_frames, matrix_to_column_list


STORAGE = get_opensurfaces_storage()


class PhotoSceneCategory(EmptyModelBase):
    """ Scene category, such as 'kitchen', 'bathroom', 'living room' """

    #: Scene category name
    name = models.CharField(max_length=127)

    #: Text description of this category
    description = models.TextField(blank=True)

    #: "Parent" category.  Scene categories can be nested in a tree.  Currently none are.
    parent = models.ForeignKey('self', blank=True, null=True)

    def __unicode__(self):
        return self.name

    def name_capitalized(self):
        return self.name[0].upper() + self.name[1:]

    def photo_count(self, **filters):
        qset = self.photos.filter(**Photo.DEFAULT_FILTERS)
        if filters:
            qset = qset.filter(**filters)
        return qset.count()

    class Meta:
        verbose_name = "Photo scene category"
        verbose_name_plural = "Photo scene categories"
        ordering = ['name']


class FlickrUser(EmptyModelBase):
    """ Flickr user """

    #: flickr username
    username = models.CharField(max_length=127)

    display_name = models.CharField(max_length=255, blank=True)

    # name shown below the display name
    sub_name = models.CharField(max_length=255, blank=True)

    given_name = models.CharField(max_length=255, blank=True)
    family_name = models.CharField(max_length=255, blank=True)

    # personal website
    website_name = models.CharField(max_length=1023, blank=True)
    website_url = models.URLField(max_length=1023, blank=True)

    #: if true, this user has too many bogus photos and will be ignored
    blacklisted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.username


class PhotoLightStack(EmptyModelBase):
    """ A collection of photos that are of an identical scene and viewpoint,
    but with different lighting conditions """

    slug = models.CharField(max_length=255, unique=True)


class Photo(UserBase):
    """
    Photograph
    """

    #: original uploaded image (jpg format)
    image_orig = models.ImageField(upload_to='photos', storage=STORAGE)

    #: Options for thumbnails.
    #: **Warning**: changing this will change the hash on all image thumbnails and you will need to re-resize every photo in the database.
    _THUMB_OPTS = {
        'source': 'image_orig',
        'format': 'JPEG',
        'options': {'quality': 90},
        'cachefile_storage': STORAGE,
    }

    #: The photograph resized to fit inside the rectangle 200 x 400
    image_200 = ImageSpecField([ResizeToFit(200, 2 * 200)], **_THUMB_OPTS)
    #: The photograph resized to fit inside the rectangle 300 x 600
    image_300 = ImageSpecField([ResizeToFit(300, 2 * 300)], **_THUMB_OPTS)

    #: The photograph resized to fit inside the rectangle 512 x 1024
    image_512 = ImageSpecField([ResizeToFit(512, 2 * 512)], **_THUMB_OPTS)
    #: The photograph resized to fit inside the rectangle 1024 x 2048
    image_1024 = ImageSpecField([ResizeToFit(1024, 2 * 1024)], **_THUMB_OPTS)
    #: The photograph resized to fit inside the rectangle 2048 x 4096
    image_2048 = ImageSpecField([ResizeToFit(2048, 2 * 2048)], **_THUMB_OPTS)

    #: The photograph cropped (and resized) to fit inside the square 300 x 300
    image_square_300 = ImageSpecField([SmartResize(300, 300)], **_THUMB_OPTS)

    #: width of ``image_orig``
    orig_width = models.IntegerField(null=True)

    #: height of ``image_orig``
    orig_height = models.IntegerField(null=True)

    #: width/height aspect ratio
    aspect_ratio = models.FloatField(null=True)

    #: optional user description
    description = models.TextField(blank=True)

    #: exif data (output from jhead)
    exif = models.TextField(blank=True)

    #: field of view in degrees of the longer dimension
    fov = models.FloatField(null=True)

    #: focal length in units of height (focal_pixels = height * focal_y)
    focal_y = models.FloatField(null=True)

    #: copyright license
    license = models.ForeignKey(
        License, related_name='photos', null=True, blank=True)

    #: the light stack that this photo is part of (most photos will not be part of one)
    light_stack = models.ForeignKey(
        PhotoLightStack, related_name='photos', null=True, blank=True)

    #: if true, this is synthetic or otherwise manually inserted for special
    #: experiments.
    synthetic = models.BooleanField(default=False)

    #: If True, this photo contains sexual content.
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    inappropriate = models.NullBooleanField()

    #: If True, this photo was NOT taken with a perspective lens (e.g. fisheye).
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    nonperspective = models.NullBooleanField()

    #: Tf True, this photo does not represent what the scene really looks like
    #: from a pinhole camera.  For example, it may have been visibly edited or
    #: is obviously HDR, or has low quality, high noise, excessive blur,
    #: excessive defocus, visible vignetting, long exposure effects, text
    #: overlays, timestamp overlays, black/white borders, washed out colors,
    #: sepia tone or black/white, infrared filter, very distorted tones (note
    #: that whitebalanced is a separate field), or some other effect.
    #:
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    stylized = models.NullBooleanField()

    #: If True, this photo is incorrectly rotated (tilt about the center).
    #: looking up or down does not count as 'rotated'.  This label is
    #: subjective; the image has to be tilted by more than 30 degrees to be
    #: labeled 'rotated'.  The label is mostly intended to capture
    #: images that are clearly 90 degrees from correct.
    #: If None, this photo has not been examined for this attribute.
    #: This field is set by admins, not workers, by visually judging the image.
    #: (this is not a limitation; we just didn't think to make this a task
    #: until late in the project)
    rotated = models.NullBooleanField()

    #: scene, e.g. "bathroom", "living room"
    scene_category = models.ForeignKey(
        PhotoSceneCategory, related_name='photos', null=True, blank=True)

    #: if true, the scene category is valid; null: unknown
    scene_category_correct = models.NullBooleanField()
    #: further from 0: more confident in assignment of scene_category_correct
    scene_category_correct_score = models.FloatField(blank=True, null=True)
    #: method used to set scene_category_correct
    scene_category_correct_method = models.CharField(
        max_length=1, choices=ResultBase.QUALITY_METHODS,
        blank=True, null=True)

    #: if true, this photo is whitebalanced; null: unknown
    whitebalanced = models.NullBooleanField()
    #: further from 0: more confident in assignment of whitebalanced
    whitebalanced_score = models.FloatField(blank=True, null=True)

    #: flickr user that uploaded this photo
    flickr_user = models.ForeignKey(
        FlickrUser, related_name='photos', null=True, blank=True)

    #: flickr photo id
    flickr_id = models.CharField(max_length=64, null=True, blank=True)

    #: name of photographer or source, if not a Flickr user
    attribution_name = models.CharField(max_length=127, blank=True)
    attribution_url = models.URLField(blank=True)

    #: hash for simple duplicate detection
    md5 = models.CharField(max_length=32)

    #: This is not "vanishing lines" in the sense that it is an infinite line
    #: passing through the vanishing point.  Rather, this is a list of line
    #: *segments* detected in the image, classified as likely passing through a
    #: certain vanishing point.
    #:
    #: json-encoded list of groups.  Each group: list of lines.  Each line: x1,
    #: y1, x2, y2 normalized by width and height.  The groups are stored in
    #: order of decreasing size.
    vanishing_lines = models.TextField(blank=True)

    #: Vanishing points, json-encoded.  Format: list of normalized (x, y) tuples.
    vanishing_points = models.TextField(blank=True)

    #: Sum of the length of all vanishing line segments (vanishing_lines).
    vanishing_length = models.FloatField(blank=True, null=True)

    #: cache of the number of correct material shapes
    #: for this photo (useful optimization when sorting by this count).
    #: These values are updated by the celery task
    #: photos.tasks.update_photos_num_shapes()
    num_shapes = models.IntegerField(default=0)

    #: cache of the number of vertices in all correct material shapes
    #: for this photo (useful optimization when sorting by this count).
    #: These values are updated by the celery task
    #: photos.tasks.update_photos_num_shapes()
    num_vertices = models.IntegerField(default=0)

    #: if True, this is part of the IIW ("Intrinsic Images in the Wild" paper) dataset.
    in_iiw_dataset = models.BooleanField(default=False)

    #: if True, this is part of the IIW ("Intrinsic Images in the Wild" paper) dense dataset.
    in_iiw_dense_dataset = models.BooleanField(default=False)

    #: cache of the number of intrinsic comparisons with nonzero score
    num_intrinsic_comparisons = models.IntegerField(default=0)

    #: cache of the number of intrinsic points (all points)
    num_intrinsic_points = models.IntegerField(default=0)

    #: median intrinsic images error
    median_intrinsic_error = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = "Photos"
        ordering = ['aspect_ratio', '-id']

    #: Default filters for views
    DEFAULT_FILTERS = {
        'synthetic': False,
        'inappropriate': False,
        'rotated': False,
        'stylized': False,
        'nonperspective': False,
        'scene_category_correct': True,
        'scene_category_correct_score__isnull': False,
        'license__creative_commons': True,
    }

    def save(self, *args, **kwargs):
        if not self.md5:
            self.md5 = md5sum(self.image_orig)

        if not self.orig_width or not self.orig_height:
            self.orig_width = self.image_orig.width
            self.orig_height = self.image_orig.height

        if not self.aspect_ratio:
            self.aspect_ratio = (float(self.image_orig.width) /
                                 float(self.image_orig.height))

        if not self.focal_y and self.fov:
            dim = max(self.image_orig.width, self.image_orig.height)
            self.focal_y = 0.5 * dim / (self.image_orig.height *
                                        math.tan(math.radians(self.fov / 2)))

        if not self.license and self.flickr_user and self.flickr_id:
            self.license = License.get_for_flickr_photo(
                self.flickr_user, self.flickr_id)

        super(Photo, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.image_orig.url

    def get_absolute_url(self):
        return reverse('photos.views.photo_detail', args=[str(self.id)])

    def get_flickr_url(self):
        if self.flickr_id and self.flickr_user_id:
            return "http://www.flickr.com/photos/%s/%s/" % (
                self.flickr_user.username, self.flickr_id)
        else:
            return None

    def image_height(self, width):
        """ Returns the height of image_<width> """
        return min(2 * width, width / self.aspect_ratio)

    def open_image(self, width='orig'):
        """ Fetch the image at a given size (see the image_<width> fields) """
        cache_attr = '_cache_image_%s' % width
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)
        pil = open_image(getattr(self, 'image_%s' % width))
        setattr(self, cache_attr, pil)
        return pil

    def get_pixel(self, x, y, width='orig'):
        """ Fetch a pixel, in floating point coordinates (x and y range from
        0.0 inclusive to 1.0 exclusive), at a given resolution (specified by
        width) """
        pil = self.open_image(width=width)
        x = float(x) * pil.size[0]
        y = float(y) * pil.size[1]
        return pil.getpixel((x, y))

    def font_size_512(self):
        """ Helper for svg templates: return the font size that should be used to
        render an image with width 512px, when in an SVG environment that has
        the height scaled to 1.0 units """
        return 10.0 / self.height_512()

    def font_adjustment_512(self):
        """ Helper for svg templates """
        return self.font_size_512() * 0.3

    def height_1024(self):
        """ Helper for templates: return the image height when the width is 1024 """
        return self.image_height(1024)

    def height_512(self):
        """ Helper for templates: return the image height when the width is 512 """
        return self.image_height(512)

    def publishable(self):
        """ True if the license exists and has publishable=True """
        return self.license and self.license.publishable

    def publishable_score(self):
        """ Return a score indicating how 'open' the photo license is """
        if not self.license:
            return 0
        return self.license.publishable_score()

    @staticmethod
    def get_thumb_template():
        return 'photos/thumb.html'

    def get_entry_dict(self):
        """ Return a dictionary of this model containing just the fields needed
        for javascript rendering.  """

        # generating thumbnail URLs is slow, so only generate the ones
        # that will definitely be used.
        return {
            'id': self.id,
            'fov': self.fov,
            'aspect_ratio': self.aspect_ratio,
            'image': {
                #'200': self.image_200.url,
                #'300': self.image_300.url,
                #'512': self.image_512.url,
                '1024': self.image_1024.url,
                '2048': self.image_2048.url,
                'orig': self.image_orig.url,
            }
        }

    def valid_material_shapes(self):
        return self.material_shapes.filter(invalid=False)

    def vanishing_points_enumerate(self):
        """ Return the vanishing points as an enumerated python list """
        return enumerate(json.loads(self.vanishing_points))

    def vanishing_vectors_enumerate(self):
        """ Return the vanishing vectors as an enumerated python list """
        return enumerate(self.vanishing_vectors())

    def vanishing_lines_svg_path(self):
        """ Generator for all vanishing line segments as SVG path data """
        if self.vanishing_lines:
            clusters = json.loads(self.vanishing_lines)
            points = json.loads(self.vanishing_points)
            for idx, lines in enumerate(clusters):
                x, y = points[idx]
                yield (
                    idx, u"".join([u"M%s,%sL%s,%s" % tuple(l) for l in lines]),
                    u"".join([u"M%s,%sL%s,%s" % (x, y, 0.5 * (l[0] + l[2]), 0.5 * (l[1] + l[3]))
                              for l in lines]))

    def vanishing_point_to_vector(self, v, focal_y=None):
        """ Return the 3D unit vector corresponding to a vanishing point
        (specified in normalized coordinates) """
        if not focal_y:
            focal_y = self.focal_y
        return normalized((
            (v[0] - 0.5) * self.aspect_ratio,
            0.5 - v[1],  # flip y coordinate
            -focal_y
        ))

    def vector_to_vanishing_point(self, v, focal_y=None):
        """ Return the 2D vanishing point (in normalized coordinates)
        corresponding to 3D vector """
        if not focal_y:
            focal_y = self.focal_y
        if abs(v[2]) < 1e-10:
            return (
                0.5 + v[0] * (focal_y / self.aspect_ratio) * 1e10,
                0.5 - v[1] * focal_y * 1e10,  # flip y coordinate
            )
        else:
            return (
                0.5 + v[0] * (focal_y / self.aspect_ratio) / (-v[2]),
                0.5 - v[1] * focal_y / (-v[2]),  # flip y coordinate
            )

    def vanishing_vectors(self, focal_y=None):
        """ Returns vanishing points as unit vectors (converted to tuples for
        compatibility with templates) """
        return [tuple(self.vanishing_point_to_vector(v, focal_y))
                for v in json.loads(self.vanishing_points)]

    def vanishing_uvn_matrices(self, focal_y=None):
        return construct_all_uvn_frames(
            self.vanishing_vectors(focal_y))

    def vanishing_uvn_matrices_json(self, focal_y=None):
        return json.dumps([
            matrix_to_column_list(m)
            for m in self.vanishing_uvn_matrices(focal_y)
        ])

    def intrinsic_densities(self):
        densities = {}
        points = self.intrinsic_points.all()
        for p in points:
            if p.min_separation in densities:
                d = densities[p.min_separation]
                d['points'].append(p)
            else:
                densities[p.min_separation] = {
                    'points': [p],
                    'comparisons': []
                }
        comparisons = self.intrinsic_comparisons.all() \
            .select_related('point1', 'point2')
        for c in comparisons:
            densities[c.point1.min_separation]['comparisons'].append(c)
        return densities

    #def best_intrinsic_images_decompositions(self):
        #""" Return the best decomposition per each type of Active algorithm """

        #qset = self.intrinsic_images_decompositions \
            #.filter(algorithm__active=True, mean_error__isnull=False) \
            #.order_by('mean_error') \
            #.select_related('algorithm')
        #alg_slugs = set()
        #ret = []
        #for d in qset:
            #if d.algorithm.slug not in alg_slugs:
                #alg_slugs.add(d.algorithm.slug)
                #ret.append(d)
        #return ret

    def best_intrinsic_images_decompositions(self):
        return self.intrinsic_images_decompositions \
            .filter(algorithm__iiw_best=True) \
            .order_by('mean_error', 'runtime')

    def intrinsic_circle_size(self):
        return self.aspect_ratio * 0.01


##
## Photo Labels
##


class PhotoLabelBase(ResultBase):
    """ Abstract parent for photo labels """

    def save(self, *args, **kwargs):
        if not self.reward:
            self.reward = compute_label_reward(self)
        super(PhotoLabelBase, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['photo', '-time_ms']

    @staticmethod
    def get_thumb_template():
        return 'photos/label_thumb.html'

    def get_thumb_overlay(self):
        return self.__unicode__()


class PhotoSceneQualityLabel(PhotoLabelBase):
    """ Label indicating whether a photo's scene category is correct. """
    photo = models.ForeignKey(Photo, related_name='scene_qualities')
    correct = models.BooleanField(default=False)

    def __unicode__(self):
        return '%s: %s %s' % (self.correct, self.photo.scene_category, self.photo)

    def get_thumb_overlay(self):
        return '%s: %s' % (self.photo.scene_category.name
                           if self.photo.scene_category else 'None', self.correct)

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #if any(l.photo.scene_category_correct_score is None for l in labels):
            #return None
        #bad = sum(1 for l in labels
                  #if l.correct != l.photo.scene_category_correct)
        #return float(bad) / float(len(labels))

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):

        if unicode(version) != u'1.0':
            raise ValueError(
                "Unknown version: '%s' (type: %s)" % (version, type(version)))
        if not hit_contents:
            return {}

        # best we can do is average
        avg_time_ms = time_ms / len(hit_contents)
        avg_time_active_ms = time_active_ms / len(hit_contents)

        new_objects = {}
        for photo in hit_contents:
            correct = (str(results[unicode(photo.id)]).lower() == 'true')

            new_obj, created = photo.scene_qualities.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=avg_time_ms,
                time_active_ms=avg_time_active_ms,
                correct=correct)

            if created:
                new_objects[get_content_tuple(photo)] = [new_obj]

        return new_objects


class PhotoWhitebalanceLabel(PhotoLabelBase):
    """ List of points in an image that should have zero chromaticity.  """

    #: photo for this whitebalance label
    photo = models.ForeignKey(Photo, related_name='whitebalances')

    #: Point format: x1,y1,x2,y2 as a fraction of width,height
    points = models.TextField(blank=True)
    #: number of points
    num_points = models.IntegerField()

    #: Median 2-norm of the a,b channel in L*a*b*, null if num_points = 0
    chroma_median = models.FloatField(null=True, blank=True)

    # :true if chroma_median < 15 and num_points > 0
    whitebalanced = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.whitebalanced = (self.chroma_median < 15 and self.num_points > 0)
        super(PhotoWhitebalanceLabel, self).save(*args, **kwargs)

    def __unicode__(self):
        #return u'added: %s, now: %s, median chroma: %s' % (self.added, now(), self.chroma_median)
        return u'median chroma: %s' % (self.chroma_median)

    def get_thumb_overlay(self):
        return 'WB' if self.whitebalanced else 'not WB'

    def get_points_aspect(self):
        """ Returns the points with the x coordinate scaled to have
        the correct aspect ratio """
        points_trim = self.points.strip()
        if points_trim:
            s = [float(f) for f in points_trim.split(',')]
            s = zip(s[::2], s[1::2])
            aspect = self.photo.aspect_ratio
            return [(x * aspect, y) for x, y in s]
        else:
            return []

    #@classmethod
    #def mturk_badness(cls, mturk_assignment):
        #""" Return fraction of bad responses for this assignment """
        #labels = cls.objects.filter(mturk_assignment=mturk_assignment)
        #if not labels:
            #return None
        #if any(l.photo.whitebalanced_score is None for l in labels):
            #return None
        #bad = sum(1 for l in labels
                  #if (l.whitebalanced != l.photo.whitebalanced and
                      #l.time_ms < 4000))
        #return float(bad) / float(len(labels))

    @staticmethod
    def mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version,
                     mturk_assignment=None, **kwargs):

        if unicode(version) != u'1.0':
            raise ValueError("Unknown version: '%s'" % version)
        if not hit_contents:
            return {}

        new_objects = {}
        for photo in hit_contents:
            points = results[unicode(photo.id)].strip()
            photo_time_ms = time_ms[unicode(photo.id)]
            photo_time_active_ms = time_active_ms[unicode(photo.id)]

            # null by default
            chroma_median = None

            # count points
            points_list = points.split(',')
            num_points = len(points_list)
            if num_points < 2:
                num_points = 0
            else:
                if num_points % 2 != 0:
                    raise ValueError(
                        "Odd number of coordinates (%d)" % num_points)
                num_points //= 2

            # compute median chromaticity
            if num_points > 0:
                pil = photo.open_image(width='300')
                chromaticities = []
                for idx in xrange(num_points):
                    x = float(points_list[idx * 2]) * pil.size[0]
                    y = float(points_list[idx * 2 + 1]) * pil.size[1]
                    rgb = pil.getpixel((x, y))
                    if rgb[0] >= 253 and rgb[1] >= 253 and rgb[2] >= 253:
                        continue  # oversaturated
                    lab = RGBColor(rgb[0], rgb[1], rgb[2]).convert_to('lab')
                    chroma = math.sqrt(
                        lab.lab_a * lab.lab_a + lab.lab_b * lab.lab_b)
                    chromaticities.append(chroma)
                if chromaticities:
                    chromaticities.sort()
                    chroma_median = chromaticities[len(chromaticities) // 2]

            # add whitebalance label
            new_obj, created = photo.whitebalances.get_or_create(
                user=user,
                mturk_assignment=mturk_assignment,
                time_ms=photo_time_ms,
                time_active_ms=photo_time_active_ms,
                points=points,
                num_points=num_points,
                chroma_median=chroma_median)

            # update photo filter status
            if created:
                new_objects[get_content_tuple(photo)] = [new_obj]

        return new_objects
