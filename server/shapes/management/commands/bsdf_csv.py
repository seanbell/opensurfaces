import csv
from clint.textui import progress

from django.core.management.base import BaseCommand

from shapes.models import MaterialShape
from bsdfs.models import ShapeBsdfLabel_wd


class Command(BaseCommand):
    args = ''
    help = 'Helper to export CSV data'

    def handle(self, *args, **options):
        print 'Fetching data...'
        qset = MaterialShape.objects.filter(
            correct=True,
            bsdf_wd__color_correct=True,
            bsdf_wd__gloss_correct=True,
            bsdf_wd__init_method='KR',
            photo__scene_category_correct_score__gt=0,
        )

        shapes = qset.values_list(
            'id',
            'photo__scene_category__name',
            'photo__scene_category_correct_score',
            'substance__name',
            'name__name',
            'planar',
            'bsdf_wd',
        )

        bsdfs = ShapeBsdfLabel_wd.objects.in_bulk(
            qset.values_list('bsdf_wd', flat=True)
        )

        filename = args[0] if len(args) >= 1 else 'out.csv'
        print 'Writing data to %s...' % filename
        with open(filename, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow([
                'shape_id',
                'scene',
                'scene_correct_score',
                'material_name',
                'object_name',
                'planar',
                'bsdf_wd_id',
                'rho_d_r',
                'rho_d_g',
                'rho_d_b',
                'rho_s_r',
                'rho_s_g',
                'rho_s_b',
                'alpha',
                'colored_reflection',
                'color_correct_score',
                'gloss_correct_score',
            ])
            for shape in progress.bar(shapes):
                b = bsdfs[shape[6]]
                rho = b.rho()
                writer.writerow(
                    list(shape) +
                    list(rho[0]) +
                    list(rho[1]) +
                    [b.alpha(), b.metallic, b.color_correct_score, b.gloss_correct_score]
                )
