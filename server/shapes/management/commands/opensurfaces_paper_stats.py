import math
from clint.textui import progress
from collections import Counter

from django.core.management.base import BaseCommand

from photos.models import *
from shapes.models import *
from mturk.models import *


def values(m, k):
    return m.values_lust(k, flat=True)


def nvalues(m, k):
    return len(set(values(m, k)))


def mean(l):
    return sum(l) / len(l)


def time_ms(m):
    return values(m.objects.filter(mturk_assignment__status__isnull=False), 'time_ms')


def wage(mean_time_ms, pay):
    return pay * 3600 * 1000 / mean_time_ms


def experiment_assignments(task, target):
    return MtAssignment.objects.filter(
        status__isnull=False,
        hit__hit_type__experiment__task=task,
        hit__hit_type__experiment__target=target)


def total_pay(assignments):
    return sum(a.hit.hit_type.reward for a in assignments)


def content_count(assignments):
    return sum(a.hit.contents.count() for a in assignments)


def mean_pay(task, target):
    assignments = experiment_assignments(task, target)
    return total_pay(assignments) / content_count(assignments)


def variance(l):
    n = len(l)
    m = sum(l) / n
    return sum([(v - m) * (v - m) for v in l]) / (n - 1)


def normal_variance(l):
    x, y, z = 0, 0, 0
    for v in l:
        x += v[8]
        y += v[9]
        z += v[10]
    length = math.sqrt(x*x + y*y + z*z)
    x /= length
    y /= length
    z /= length

    dangle = 0
    for v in l:
        length = math.sqrt(v[8] * v[8] + v[9] * v[9] + v[10] * v[10])
        dot = (v[8] * x + v[9] * y + v[10] * z) / length
        dot = max(-1, min(1, dot))
        angle = math.degrees(math.acos(dot))
        dangle += angle * angle

    return dangle / (len(l) - 1)


def row(label, qset, nin, nout):
    qset2 = qset.filter(mturk_assignment__hit__hit_type__reward__isnull=False).filter(time_ms__isnull=False).order_by()
    t = mean(filter(None, qset2.order_by().values_list('time_ms', flat=True))) * 1.10
    p = sum(qset2.distinct('mturk_assignment').values_list(
        'mturk_assignment__hit__hit_type__reward', flat=True)) / qset2.count()
    #if label == 'Segmentation':
        #print '%s & %0.2f c & %0.2f s & %s & %s \\\\' % (
            #label, p * 100, t / 1000.0, '{:,}'.format(nin), '{:,}'.format(nout) if nout else 'N/A')
    #else:
    print r'%s & \$%0.4f & %0.1f s & %s & %s & %s \\' % (
        label, p, t / 1000.0, '{:,}'.format(nin), '{:,}'.format(nout) if nout else 'N/A',
        r'%0.1f\%%' % (100.0 * nout / nin) if nout and nout <= nin else 'N/A')


class Command(BaseCommand):
    args = ''
    help = 'Manages the mturk pipeline'

    def handle(self, *args, **options):
        self.task_table()
        return
        self.cubam_change()
        self.variance_cd()
        self.variance_tex()

    def cubam_change(self):
        scene_quality = [[0, 0], [0, 0]]
        for p in Photo.objects.all():
            count = p.scene_qualities.count()
            if count > 0:
                cubam = int(p.scene_category_correct is True)
                maj = p.scene_qualities.filter(correct=True).count() > 0.5 * count
                scene_quality[cubam][maj] += 1
        print 'scene_quality:'
        m = scene_quality
        print '%s %s' % (m[0][0], m[0][1])
        print '%s %s' % (m[1][0], m[1][1])

        whitebalance = [[0, 0], [0, 0]]
        for p in Photo.objects.all():
            count = p.whitebalances.count()
            if count > 0:
                cubam = int(p.whitebalanced is True)
                maj = p.whitebalances.filter(whitebalanced=True).count() > 0.5 * count
                whitebalance[cubam][maj] += 1
        print 'whitebalance:'
        m = whitebalance
        print '%s %s' % (m[0][0], m[0][1])
        print '%s %s' % (m[1][0], m[1][1])

        shape_quality = [[0, 0], [0, 0]]
        for p in MaterialShape.objects.all():
            count = p.qualities.count()
            if count > 0:
                cubam = int(p.correct is True)
                maj = p.qualities.filter(correct=True).count() > 0.5 * count
                shape_quality[cubam][maj] += 1
        print 'shape_quality:'
        m = shape_quality
        print '%s %s' % (m[0][0], m[0][1])
        print '%s %s' % (m[1][0], m[1][1])

        planarity = [[0, 0], [0, 0]]
        for p in MaterialShape.objects.all():
            count = p.planarities.count()
            if count > 0:
                cubam = int(p.planar is True)
                maj = p.planarities.filter(planar=True).count() > 0.5 * count
                planarity[cubam][maj] += 1
        print 'planarity:'
        m = planarity
        print '%s %s' % (m[0][0], m[0][1])
        print '%s %s' % (m[1][0], m[1][1])


    def variance_tex(self):
        orig_variance = []
        filtered_variance = []

        print 'tex counts:', Counter([shape.rectified_normals.filter(admin_score__gt=0).count() for shape in
                progress.bar(MaterialShape.objects.filter(photo__synthetic=False))]).most_common()

        for shape in progress.bar(MaterialShape.objects.filter(photo__synthetic=False)):
            normals = shape.rectified_normals.all()
            if not normals or normals.count() < 1:
                continue

            phi_filtered = [json.loads(n.uvnb) for n in
                            normals.filter(admin_score__gt=0)]
            if len(phi_filtered) >= 2:
                filtered_variance.append(normal_variance(phi_filtered))

                phi_orig = [json.loads(n.uvnb) for n in normals]
                orig_variance.append(normal_variance(phi_orig))
                #print '%s --> %s' % (
                    #orig_variance[len(orig_variance) - 1],
                    #filtered_variance[len(filtered_variance) - 1])

        print 'num:', len(orig_variance)
        print 'orig_variance:', math.sqrt(mean(orig_variance))
        print 'filtered_variance:', math.sqrt(mean(filtered_variance))

    def variance_cd(self):
        print 'bsdf counts:', Counter([shape.bsdfs_wd.filter(admin_score__gt=1).count() for shape in
                progress.bar(MaterialShape.objects.filter(photo__synthetic=False))]).most_common()

        orig_variance_c = []
        filtered_variance_c = []
        orig_variance_d = []
        filtered_variance_d = []
        for shape in progress.bar(MaterialShape.objects.filter(photo__synthetic=False)):
            bsdfs = shape.bsdfs_wd.all()
            if not bsdfs or bsdfs.count() < 1:
                continue

            filtered_c = [n.c() for n in bsdfs.filter(admin_score__gt=1)]
            filtered_d = [n.d() for n in bsdfs.filter(admin_score__gt=1)]
            if len(filtered_c) >= 2 and len(filtered_d) >= 2:
                filtered_variance_c.append(variance(filtered_c))
                filtered_variance_d.append(variance(filtered_d))
                orig_variance_c.append(variance([n.c() for n in bsdfs]))
                orig_variance_d.append(variance([n.d() for n in bsdfs]))
                #print '%s --> %s' % (
                    #orig_variance_c[len(orig_variance_c) - 1],
                    #filtered_variance_c[len(filtered_variance_c) - 1])
                #print '  %s --> %s' % (
                    #orig_variance_d[len(orig_variance_d) - 1],
                    #filtered_variance_d[len(filtered_variance_d) - 1])

        print 'num:', len(orig_variance_c)
        print 'orig_variance_c:', math.sqrt(mean(orig_variance_c))
        print 'filtered_variance_c:', math.sqrt(mean(filtered_variance_c))
        print 'orig_variance_d:', math.sqrt(mean(orig_variance_d))
        print 'filtered_variance_d:', math.sqrt(mean(filtered_variance_d))

    def task_table(self):
        #print r'\textbf{Task} & \textbf{Pay/item} & $\textbf{Time}$ & $\mathbf{n_\text{in}}$ & $\mathbf{\% good}$ \\'

        nin = PhotoSceneQualityLabel.objects.all().distinct('photo').count()
        nout = Photo.objects.filter(scene_category_correct=True).count()
        qset = PhotoSceneQualityLabel.objects.all()
        row('Scene curation', qset, nin, nout)

        nin = Photo.objects.filter(scene_category_correct=True, whitebalanced_score__isnull=False).count()
        nout = Photo.objects.filter(scene_category_correct=True, whitebalanced=True).count()
        qset = PhotoWhitebalanceLabel.objects.all()
        row('White balance', qset, nin, nout)

        nin = MaterialShape.objects.all().distinct('photo').count()
        nout = MaterialShape.objects.all().count()
        qset = MaterialShape.objects.all()
        row('Segmentation', qset, nin, nout)

        nin = MaterialShape.objects.filter(correct_score__isnull=False).count()
        nout = MaterialShape.objects.filter(correct_score__gt=0).count()
        qset = MaterialShapeQuality.objects.all()
        row('Segmentation Quality', qset, nin, nout)

        nin = MaterialShape.objects.filter(correct=True, substances__isnull=False).distinct('id').count()
        nout = MaterialShape.objects.filter(correct=True, substance__isnull=False).count()
        qset = ShapeSubstanceLabel.objects.all()
        row('Material name', qset, nin, nout)

        nin = MaterialShape.objects.filter(correct=True, names__isnull=False).distinct('id').count()
        nout = MaterialShape.objects.filter(correct=True, name__isnull=False).count()
        qset = MaterialShapeNameLabel.objects.all()
        row('Object name', qset, nin, nout)

        nin = MaterialShape.objects.filter(correct=True, planar_score__isnull=False).count()
        nout = MaterialShape.objects.filter(correct=True, planar_score__gt=0).count()
        qset = ShapePlanarityLabel.objects.all()
        row('Planarity', qset, nin, nout)

        nin = ShapeRectifiedNormalQuality.objects.distinct('rectified_normal__shape').count()
        nout = nin
        qset = ShapeRectifiedNormalLabel.objects.all()
        row('Rectification', qset, nin, nout)

        nin = ShapeRectifiedNormalQuality.objects.all().distinct('rectified_normal__shape').count()
        nout = MaterialShape.objects.filter(rectified_normal__isnull=False).count()
        qset = ShapeRectifiedNormalQuality.objects.all()
        row('Rectification Quality', qset, nin, nout)

        nin = ShapeBsdfLabel_wd.objects.filter(color_correct_score__isnull=False) \
            .distinct('shape').count()
        nout = nin
        qset = ShapeBsdfLabel_wd.objects.all()
        row('Reflectance', qset, nin, nout)

        nin = ShapeBsdfLabel_wd.objects.filter(color_correct_score__isnull=False) \
            .distinct('shape').count()
        nout = ShapeBsdfLabel_wd.objects.filter(color_correct=True) \
            .distinct('shape').count()
        qset = ShapeBsdfQuality.objects.filter(color_correct__isnull=False)
        row('Color Quality', qset, nin, nout)

        nin = ShapeBsdfLabel_wd.objects \
            .filter(color_correct=True, gloss_correct_score__isnull=False) \
            .distinct('shape').count()
        nout = ShapeBsdfLabel_wd.objects \
            .filter(color_correct=True, gloss_correct=True) \
            .distinct('shape').count()
        qset = ShapeBsdfQuality.objects.filter(gloss_correct__isnull=False)
        row('Gloss Quality', qset, nin, nout)
