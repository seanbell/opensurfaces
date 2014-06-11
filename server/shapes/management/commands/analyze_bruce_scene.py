import json
import math
from django.core.management.base import BaseCommand
from clint.textui import progress

from shapes.models import MaterialShape
from bsdfs.models import ShapeBsdfLabel_wd
from common.utils import queryset_progress_bar


class Command(BaseCommand):
    args = ''
    help = "Analyze people's quality when doing Bruce's scene"

    def handle(self, *args, **options):

        gt = {
            'teacup': 0.08,
            'coyote': 0.11,
            'spoon': 0,
        }

        for exclude_nnz in [True, False]:
            for thresh in [0.0, 0.5, 1.0]:
                print '\n\nTHRESH %s' % thresh
                for slug in ["teapot", "horse", "table", "coyote", "teacup", "teapot", "plate", "spoon"]:
                    if slug not in gt: continue

                    n_2percent = 0
                    alphas = []
                    for s in MaterialShape.objects.filter(synthetic_slug=slug):
                        bsdfs = s.bsdfs_wd.filter(color_correct=True, gloss_correct=True,
                                                color_correct_score__gt=thresh,
                                                gloss_correct_score__gt=thresh)
                        for b in bsdfs:
                            if exclude_nnz:
                                edits = json.loads(b.edit_dict)
                                if edits['doi'] < 1:
                                    continue

                            alpha = b.alpha()
                            if gt[slug] > 0 and abs(alpha - gt[slug]) / gt[slug] <= 0.025:
                                n_2percent += 1
                            alphas.append(alpha)

                    r = rmse(alphas, gt[slug])
                    print '\nexclude_nnz: %s' % exclude_nnz
                    print '%s: true: %.3f, mean: %.3f stdev: %.3f, RMSE: %.3f (%.1f %%)' % (slug, gt[slug], mean(alphas), std(alphas), r, r * 100 / 0.2)
                    print '%s: num samples = %s' % (slug, len(alphas))
                    print '%s: num within 2%% = %s' % (slug, n_2percent)
                    print ''

        shape_ids = MaterialShape.objects.all().values_list('id', flat=True)

        for exclude_nnz in [True, False]:
            for f in [False, True]:
                variances_alpha = []
                variances_c = []
                for shape_id in progress.bar(shape_ids):
                    if f:
                        bsdfs = ShapeBsdfLabel_wd.objects.filter(
                            shape_id=shape_id, color_correct=True, gloss_correct=True)
                    else:
                        bsdfs = ShapeBsdfLabel_wd.objects.filter(shape_id=shape_id)

                    alphas = []
                    for b in bsdfs:
                        if exclude_nnz:
                            edits = json.loads(b.edit_dict)
                            if edits['doi'] < 1:
                                continue
                        alphas.append(b.alpha())
                    if len(alphas) >= 2:
                        variances_alpha.append( var(alphas) )

                    c_list = []
                    for b in bsdfs:
                        if exclude_nnz:
                            edits = json.loads(b.edit_dict)
                            if edits['contrast'] < 1:
                                continue
                        c_list.append(b.c())
                    if len(c_list) >= 2:
                        variances_c.append( var(c_list) )

                print '\nexclude_nnz: %s, filter: %s, mean variance alpha: %s, c: %s' % (
                    exclude_nnz, f, mean(variances_alpha), mean(variances_c))



def mean(l):
    if not l: return float('NaN')
    return sum(l) / len(l)

def var(l):
    if len(l) < 2: return float('NaN')
    m = mean(l)
    return sum((x - m) * (x - m) for x in l) / (len(l) - 1)

def std(l):
    return math.sqrt(var(l))

def rmse(l, gt):
    if len(l) < 1: return float('NaN')
    return math.sqrt( sum((x-gt) * (x-gt) for x in l) / len(l) )
