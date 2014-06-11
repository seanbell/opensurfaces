import csv
import json

from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import ensure_csrf_cookie

from cacheback.decorators import cacheback
from endless_pagination.decorators import page_template

from common.utils import dict_union, prepare_votes_bar, \
    json_error_response
from photos.views import photo_scene_categories
from shapes.models import Shape, MaterialShape, \
    ShapeSubstance, ShapeName
from shapes.utils import get_similar_shapes
from accounts.models import UserProfile


@page_template('grid4_page.html')
def material_shape_all(
        request, template='endless_list.html', extra_context=None):

    entries = MaterialShape.objects.all() \
        .select_related('photo') \
        .order_by('-added')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'all',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_thumb.html',
        'header': 'All submissions',
        'header_small': 'sorted by submission time',
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_by_time(
        request, template='endless_list.html', extra_context=None):

    entries = MaterialShape.objects \
        .filter(**MaterialShape.DEFAULT_FILTERS) \
        .select_related('photo') \
        .order_by('-time_ms', '-correct_score')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-time',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_thumb.html',
        'header': 'Submissions',
        'header_small': 'sorted by worker time',
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_by_vertices(
        request, template='endless_list.html', extra_context=None):

    entries = MaterialShape.objects \
        .filter(**MaterialShape.DEFAULT_FILTERS) \
        .select_related('photo') \
        .order_by('-num_vertices', '-correct_score')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-vertices',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_thumb.html',
        'header': 'Submissions',
        'header_small': 'sorted by vertex count',
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_by_quality(request,
                              template='endless_list_votes.html',
                              extra_context=None):

    entries = MaterialShape.objects \
        .filter(pixel_area__gt=Shape.MIN_PIXEL_AREA,
                correct_score__isnull=False,
                synthetic=False) \
        .select_related('photo') \
        .order_by('-correct_score', '-area')  # '-num_vertices', '-time_ms')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-quality',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_quality_thumb.html',
        'header': 'Submissions',
        'header_small': 'sorted by quality votes',
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_by_planarity(request,
                                template='endless_list_votes.html',
                                extra_context=None):

    entries = MaterialShape.objects \
        .filter(pixel_area__gt=Shape.MIN_PIXEL_AREA,
                correct=True,
                planar_score__isnull=False,
                synthetic=False) \
        .select_related('photo') \
        .order_by('-planar_score', '-area')  # , '-num_vertices', '-time_ms')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-planarity',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_planarity_thumb.html',
        'header': 'Submissions',
        'header_small': 'sorted by planarity votes',
    }, extra_context)

    return render(request, template, context)


@staff_member_required
@page_template('grid4_page.html')
def material_shape_curate_planarity(
        request, template='endless_list_curate.html', extra_context=None):

    entries = MaterialShape.objects \
        .filter(planar=True, correct=True) \
        .select_related('photo') \
        .order_by('-num_vertices', 'planar_score')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'curate-planarity',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_thumb.html',
        'header': 'Submissions',
        'header_small': 'sorted by planarity votes',
        'curate_post_url': reverse('material-shape-curate-planarity-post'),
    }, extra_context)

    return render(request, template, context)


@require_POST
@staff_member_required
def material_shape_curate_planarity_post(request):
    if request.POST['model'] != "shapes/materialshape":
        return json_error_response("invalid model")
    shape = MaterialShape.objects.get(id=request.POST['id'])
    shape.planar_method = 'A'
    shape.planar = not shape.planar
    shape.save()
    return HttpResponse(
        json.dumps({'selected': not shape.planar}),
        mimetype='application/json')


@page_template('grid4_page.html')
def material_shape_by_substance(request, template='endless_list.html',
                                extra_context=None):

    entries = MaterialShape.objects \
        .filter(**MaterialShape.DEFAULT_FILTERS) \
        .filter(substance_entropy__isnull=False) \
        .select_related('photo') \
        .order_by('substance_entropy', '-correct_score')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-substance',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_substance_thumb.html',
        'header': 'Submissions',
        'header_small': 'sorted by entropy',
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_by_name(request, template='endless_list.html',
                           extra_context=None):

    entries = MaterialShape.objects \
        .filter(pixel_area__gt=Shape.MIN_PIXEL_AREA,
                correct=True,
                name_entropy__isnull=False,
                synthetic=False) \
        .select_related('photo') \
        .order_by('name_entropy', '-correct_score')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-name',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_name_thumb.html',
        'header': 'Submissions',
        'header_small': 'sorted by entropy',
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_by_rejected(request, template='endless_list.html',
                               extra_context=None):

    entries = MaterialShape.objects \
        .filter(mturk_assignment__status='R') \
        .select_related('photo') \
        .order_by('-time_ms')
        #.order_by('-mturk_assignment__updated')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-rejected',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_thumb.html',
        'header': 'Rejected submissions',
        'header_small': 'sorted by worker time',
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_by_synthetic(request, template='endless_list.html',
                                extra_context=None):

    entries = MaterialShape.objects \
        .filter(synthetic=True) \
        .select_related('photo') \
        .order_by('-synthetic_slug', '-num_vertices')
        #.order_by('-mturk_assignment__updated')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-synthetic',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_thumb.html',
        'header': 'Special submissions',
        'header_small': 'sorted by worker time',
    }, extra_context)

    return render(request, template, context)


@page_template('material_shape_by_user_page.html')
def material_shape_by_user(request, template='material_shape_by_user.html',
                           extra_context=None):

    users = UserProfile.objects \
        .prefetch_related('materialshape_set') \
        .annotate(num_material_shapes=Count('materialshape')) \
        .order_by('-num_material_shapes')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'by-user',
        'users': users,
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def material_shape_rectified(request, template='endless_list.html',
                             extra_context=None):

    entries = MaterialShape.objects \
        .filter(**MaterialShape.DEFAULT_FILTERS) \
        .filter(planar=True, planar_score__isnull=False) \
        .exclude(image_rectified=u'') \
        .select_related('photo') \
        .order_by('-rectified_area')  # , '-num_vertices', '-time_ms')

    context = dict_union({
        'nav': 'browse/material-shape', 'subnav': 'rectified',
        'entries': entries,
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_rectified_thumb.html',
    }, extra_context)

    return render(request, template, context)


def material_shape_detail(request, pk):
    shape = get_object_or_404(MaterialShape, pk=pk)

    votes = [
        prepare_votes_bar(shape, 'qualities', 'correct',
                          'correct', 'Quality'),
        prepare_votes_bar(shape, 'planarities', 'planar',
                          'planar', 'Planarity'),
    ]

    bsdfs_wd = shape.bsdfs_wd \
        .extra(
            select={'correct_score':
                    'color_correct_score + gloss_correct_score'},
            order_by=('-correct_score',)
        )
        #.filter(color_correct=True, gloss_correct=True) \

    data = {
        'nav': 'browse/material-shape',
        'shape': shape,
        'votes': votes,
        'names': shape.names.select_related('name').filter(invalid=False),
        'substances': (shape.substances.select_related('substance')
                       .filter(invalid=False)),
        'bsdfs_wd': bsdfs_wd,
        'rectified_normals': (
            shape.rectified_normals
            .select_related('shape', 'shape__photo')
            .order_by('-correct_score'))
    }

    if shape.bsdf_wd:
        data['similar_shapes'] = get_similar_shapes(shape.bsdf_wd)

    return render(request, 'material_shape_detail.html', data)


def material_shape_all_csv(request):
    return material_shape_csv(MaterialShape.objects.all().order_by('id'))


def material_shape_csv(shapes):
    """ Return a list of material shapes formatted as a tab-separated-value file """

    response = HttpResponse(mimetype='text/csv')
    #response['Content-Disposition'] = 'attachment; filename="material-shapes.csv"'
    writer = csv.writer(response)

    # for these fields, we can use python reflection
    fields = ['id', 'user_id', 'added', 'num_vertices', 'time_ms']
    writer.writerow(fields + ['num_material_votes', 'num_bad_votes',
                    'num_planar_votes', 'num_nonplanar_votes'])

    for shape in shapes.prefetch_related('qualities'):
        row = []
        for f in fields:
            row.append(getattr(shape, f))

        votes = shape.votes_dict()
        row.append(votes['M'])
        row.append(votes['B'])
        row.append(shape.num_planar_votes())
        row.append(shape.num_nonplanar_votes())
        writer.writerow(row)

    return response


def material_shape_bsdfs_csv(request, pk, v):
    """
    Return all BSDFs_v for a given shape
    Note: pk precedes v since we are filtering by pk first
    """
    from bsdfs.models import BSDF_VERSIONS
    from bsdfs.views import bsdfs_csv

    if v not in BSDF_VERSIONS:
        raise Http404
    shape = get_object_or_404(MaterialShape, pk=pk)
    bsdfs = getattr(shape, 'bsdfs_%s' % v).all().order_by('id')
    return bsdfs_csv(v, bsdfs)


@ensure_csrf_cookie
@page_template('list_page.html')
def material_shape_search(
        request, template='material_shape_search.html', extra_context=None):

    filters = dict(MaterialShape.DEFAULT_FILTERS)

    if 'contrast' in request.REQUEST and request.REQUEST['contrast']:
        low, high = request.REQUEST['contrast'].split('-')
        if float(low) > 0:
            filters['bsdf_wd__contrast__gte'] = low
        if float(high) < 1:
            filters['bsdf_wd__contrast__lte'] = high

    if 'doi' in request.REQUEST and request.REQUEST['doi']:
        low, high = request.REQUEST['doi'].split('-')
        if int(low) > 0:
            filters['bsdf_wd__doi__gte'] = low
        if int(high) < 15:
            filters['bsdf_wd__doi__lte'] = high

    for key in ['substance', 'name', 'photo__scene_category']:
        id = request.REQUEST.get(key, 0)
        if id and int(id) > 0:
            filters[key + '_id'] = id

    for key, attr in [('planar', 'planar'),
                      ('whitebalanced', 'photo__whitebalanced')]:
        val = request.REQUEST.get(key)
        if val == 'on':
            filters[attr] = True
        elif val == 'off':
            filters[attr] = False

    for key, attr in [('has_texture', 'rectified_normal__isnull'),
                      ('has_reflectance', 'bsdf_wd__isnull')]:
        val = request.REQUEST.get(key)
        if val == 'on':
            filters[attr] = False

    order_by = request.REQUEST.get('order_by')
    if not order_by:
        order_by = 'num_vertices'
    if 'bsdf_wd' in order_by:
        filters['bsdf_wd__isnull'] = False
    if 'rectified_normal' in order_by:
        filters['bsdf_wd__isnull'] = False

    entries = MaterialShape.objects \
        .filter(**filters) \
        .order_by('-' + order_by) \
        .select_related(
            'photo', 'photo__scene_category', 'substance',
            'name', 'bsdf_wd', 'rectified_normal'
        )

    context = {
        'nav': 'material-shape-search',
        'entries': entries,
        'thumb_template': 'material_shape_row.html',
        'names': material_shape_categories(ShapeName),
        'substances': material_shape_categories(ShapeSubstance),
        'scene_categories': photo_scene_categories()['categories'],
    }

    context.update(extra_context)
    return render(request, template, context)


@cacheback(3600)
def material_shape_categories(category_model):
    """ Returns three category lists, for use with rendering """

    ret = {'categories_all': [{
        'id': 0, 'name': 'All',
        'count': MaterialShape.objects.filter(
            **MaterialShape.DEFAULT_FILTERS).count()
    }]}
    for fail in (False, True):
        lst = [
            {'id': c.id, 'name': c.name, 'count': c.material_shape_count()}
            for c in category_model.objects.filter(fail=fail)
        ]
        lst.sort(key=lambda x: x['count'], reverse=True)
        ret['categories_fail' if fail else 'categories'] = filter(lambda x: x['count'], lst)

    return ret


def render_material_shape_categories(
    request, pk, template, extra_context,
        category_model, category_attr, url_name):

    # id 0: all shapes
    pk = int(pk)
    if pk != 0:
        filters = MaterialShape.DEFAULT_FILTERS.copy()
        filters[category_attr + '_id'] = pk
    else:
        filters = MaterialShape.DEFAULT_FILTERS

    #if request.user.is_staff:
        #filters = dict_union(filters, {
            #'photo__license__publishable': True,
            #'photo__whitebalanced': True
        #})

    entries = MaterialShape.objects \
        .filter(**filters) \
        .select_related('photo', 'bsdf_wd') \
        .order_by('-num_vertices')

    if 'publishable' in request.GET:
        entries = entries.filter(photo__license__publishable=True)
    if 'whitebalanced' in request.GET:
        entries = entries.filter(photo__whitebalanced=True)

    context = {
        'nav': 'browse/%s' % category_attr,
        'subnav': 'all',
        'category_id': pk,
        'url_name': url_name,
        'entries': entries,
        'entries_per_page': 6,
        'span': 'span3',
        'rowsize': '3',
        'base_template': 'material_shape_base.html',
        'thumb_template': 'material_shape_thumb.html',
    }

    context.update(extra_context)
    context.update(material_shape_categories(category_model))

    return render(request, template, context)


@page_template('grid_page.html')
def name_all(request, pk=0,
             template='name_all.html',
             extra_context=None):

    return render_material_shape_categories(
        request, pk, template, extra_context,
        ShapeName, 'name', 'name-all')


@page_template('grid_page.html')
def substance_all(request, pk=0,
                  template='substance_all.html',
                  extra_context=None):

    return render_material_shape_categories(
        request, pk, template, extra_context,
        ShapeSubstance, 'substance', 'substance-all')
