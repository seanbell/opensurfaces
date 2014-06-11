from django.shortcuts import render

from cacheback.decorators import cacheback
from common.utils import dump_queryset_to_static_csv

from shapes.models import MaterialShape
from normals.models import ShapeRectifiedNormalLabel
from bsdfs.models import ShapeBsdfLabel_wd


@cacheback(3600)
def material_shape_csv_url():
    entries = MaterialShape.objects.filter(
        time_ms__isnull=False, correct=True)

    return dump_queryset_to_static_csv(
        entries, ['time_ms', 'num_vertices', 'planar_score'],
        'analytics/materialshape.csv')


def analytics_material_shapes(
        request, template='analytics/material_shapes.html'):
    context = {
        'nav': 'analytics',
        'subnav': 'material-shapes',
        'across': 'material shapes',
        'csv_url': material_shape_csv_url(),
    }
    return render(request, template, context)


@cacheback(3600)
def bsdf_wd_csv_url():
    entries = ShapeBsdfLabel_wd.objects.filter(
        time_ms__isnull=False, edit_nnz__gt=2)

    return dump_queryset_to_static_csv(
        entries, [
            'time_ms', 'doi', 'contrast', 'color_correct_score',
            'gloss_correct_score'
        ], 'analytics/shapebsdflabel_wd.csv')


def analytics_bsdf_wd(
        request, template='analytics/bsdf_wd.html'):
    context = {
        'nav': 'analytics',
        'subnav': 'bsdf-wd',
        'across': 'reflectances',
        'csv_url': bsdf_wd_csv_url(),
    }
    return render(request, template, context)


@cacheback(3600)
def rectified_normal_csv_url():
    entries = ShapeRectifiedNormalLabel.objects.filter(
        time_ms__isnull=False, automatic=False)

    return dump_queryset_to_static_csv(
        entries, ['time_ms', 'correct_score'],
        'analytics/shaperectifiednormallabel.csv')


def analytics_rectified_normal(
        request, template='analytics/rectified_normal.html'):
    context = {
        'nav': 'analytics',
        'subnav': 'rectified-normal',
        'across': 'textures',
        'csv_url': rectified_normal_csv_url(),
    }
    return render(request, template, context)
