import csv

from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.db.models.loading import get_model
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.contenttypes.models import ContentType

from endless_pagination.decorators import page_template

from common.utils import dict_union, \
    prepare_votes_bar_impl, json_success_response
from bsdfs.models import ShapeBsdfQuality, BSDF_VERSIONS


def bsdf_all_csv(request, v):
    """ Return ``bsdfs_csv()`` for all BSDFS """
    if v not in BSDF_VERSIONS:
        raise Http404
    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    return bsdfs_csv(v, bsdf_model.objects.all().order_by('id'))


def bsdfs_csv(v, bsdfs):
    """ Return a list of BSDFs formatted as a tab-separated-value file """
    if v not in BSDF_VERSIONS:
        raise Http404

    response = HttpResponse(mimetype='text/csv')
    #response['Content-Disposition'] = 'attachment; filename="bsdfs.csv"'
    writer = csv.writer(response)

    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    fields = [f.name for f in bsdf_model._meta.fields]
    writer.writerow(fields)

    for bsdf in bsdfs:
        row = []
        for name in fields:
            value = getattr(bsdf, name)
            if hasattr(value, 'isoformat'):
                row.append(value.isoformat())
            else:
                row.append(value)
        writer.writerow(row)

    return response


@page_template('grid4_page.html')
def bsdf_all(request, v, template='endless_list.html', extra_context=None):
    if v not in BSDF_VERSIONS:
        raise Http404

    entries = get_model('bsdfs', 'ShapeBsdfLabel_' + v).objects.all() \
        .filter(time_ms__isnull=False, shape__photo__inappropriate=False) \
        .order_by('-id')

    context = dict_union({
        'nav': 'browse/bsdf-%s' % v, 'subnav': 'all',
        'entries': entries,
        'base_template': 'bsdf_base.html',
        'thumb_template': 'bsdf_%s_shape_thumb.html' % v,
        'header': 'All submissions',
        'header_small': 'sorted by date',
        'v': v,
        #'enable_voting': False,
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def bsdf_good(request, v, template='endless_list.html', extra_context=None):
    if v not in BSDF_VERSIONS:
        raise Http404

    entries = get_model('bsdfs', 'ShapeBsdfLabel_' + v).objects.all() \
        .filter(color_correct=True, gloss_correct=True,
                shape__photo__inappropriate=False,
                shape__bsdf_wd_id=F('id')) \

    if 'by-id' in request.GET:
        header_small = 'sorted by id'
        entries = entries.order_by('-id')
    else:
        header_small = 'sorted by quality'
        entries = entries.extra(
            select={'correct_score':
                    'color_correct_score + gloss_correct_score'},
            order_by=('-correct_score',)
        ) \

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = dict_union({
        'nav': 'browse/bsdf-%s' % v, 'subnav': 'good',
        'entries': entries,
        'base_template': 'bsdf_base.html',
        'thumb_template': 'bsdf_%s_shape_thumb.html' % v,
        'header': 'High quality submissions',
        'header_small': header_small,
        'v': v,
        #'enable_voting': False,
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def bsdf_bad(request, v, template='endless_list.html', extra_context=None):
    if v not in BSDF_VERSIONS:
        raise Http404

    entries = get_model('bsdfs', 'ShapeBsdfLabel_' + v).objects \
        .filter(shape__photo__inappropriate=False) \
        .exclude(color_correct=True) \
        .exclude(gloss_correct=True) \
        .extra(
            select={'correct_score':
                    'color_correct_score + gloss_correct_score'},
            order_by=('correct_score',)
        )
        #.filter(time_ms__isnull=False, admin_score__lt=0, shape__synthetic=False) \
        #.order_by('admin_score', '-shape__pixel_area')

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = dict_union({
        'nav': 'browse/bsdf-%s' % v, 'subnav': 'bad',
        'entries': entries,
        'base_template': 'bsdf_base.html',
        'thumb_template': 'bsdf_%s_shape_thumb.html' % v,
        'header': 'Low quality submissions',
        'header_small': 'sorted by quality',
        'v': v,
        #'enable_voting': False,
    }, extra_context)

    return render(request, template, context)


@page_template('grid4_page.html')
def bsdf_failed(request, v, template='endless_list.html', extra_context=None):
    if v not in BSDF_VERSIONS:
        raise Http404

    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    entries = bsdf_model.objects \
        .filter(give_up=True, shape__photo__inappropriate=False) \
        .order_by('-id')

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = {
        'nav': 'browse/bsdf-%s' % v, 'subnav': 'failed',
        'entries': entries,
        'base_template': 'bsdf_base.html',
        'thumb_template': 'bsdf_%s_shape_thumb.html' % v,
        'header': 'Failed submissions',
        'header_sub': 'For these submissions, the user clicked "I give up" and provided a message.',
        'v': v,
    }

    if extra_context is not None:
        context.update(extra_context)
    return render(request, template, context)


def bsdf_detail(request, v, pk):
    if v not in BSDF_VERSIONS:
        raise Http404

    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    bsdf = get_object_or_404(bsdf_model, pk=pk)

    ct = ContentType.objects.get_for_model(bsdf_model)
    votes = [
        prepare_votes_bar_impl(
            ShapeBsdfQuality.objects.filter(
                content_type=ct, object_id=pk,
                color_correct__isnull=False, invalid=False)
            .values_list('color_correct', flat=True),
            bsdf.color_correct_score,
            'Color correct'),
        prepare_votes_bar_impl(
            ShapeBsdfQuality.objects.filter(
                content_type=ct, object_id=pk,
                gloss_correct__isnull=False, invalid=False)
            .values_list('gloss_correct', flat=True),
            bsdf.gloss_correct_score,
            'Gloss correct'),
    ]

    data = {
        'nav': 'browse/bsdf-%s' % v,
        'bsdf': bsdf,
        'shape': bsdf.shape,
        'photo': bsdf.shape.photo,
        'votes': votes,
        'v': v
    }

    return render(request, 'bsdf_%s_detail.html' % v, data)


@ensure_csrf_cookie
@page_template('grid4_page.html')
def bsdf_wd_voted_none(request, template='endless_list.html',
                       extra_context=None):

    v = 'wd'
    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    entries = bsdf_model.objects \
        .filter(give_up=False, admin_score=0, time_ms__gt=500) \
        .order_by('-shape__synthetic', '-shape__pixel_area')  # '-shape__pixel_area', '-shape__correct_score')

    context = dict_union({
        'nav': 'browse/bsdf-%s' % v,
        'subnav': 'vote',
        'entries': entries,
        'base_template': 'bsdf_base.html',
        'thumb_template': 'bsdf_wd_thumb_vote.html',
        'v': v,
        'enable_voting': True,
    }, extra_context)

    return render(request, template, context)


@ensure_csrf_cookie
@page_template('grid4_page.html')
def bsdf_wd_voted_yes(request, template='endless_list.html',
                      extra_context=None):

    v = 'wd'
    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    entries = bsdf_model.objects \
        .filter(admin_score__gt=0) \
        .order_by('-admin_score', '-shape__pixel_area', '-shape__correct_score')

    context = dict_union({
        'nav': 'browse/bsdf-%s' % v,
        'subnav': 'voted-yes',
        'entries': entries,
        'base_template': 'bsdf_base.html',
        'thumb_template': 'bsdf_wd_thumb_vote.html',
        'v': v,
        'enable_voting': True,
    }, extra_context)

    return render(request, template, context)


@ensure_csrf_cookie
@page_template('grid4_page.html')
def bsdf_wd_voted_no(request, template='endless_list.html',
                     extra_context=None):

    v = 'wd'
    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    entries = bsdf_model.objects \
        .filter(admin_score__lt=0) \
        .order_by('admin_score', '-shape__pixel_area', '-shape__correct_score')

    context = dict_union({
        'nav': 'browse/bsdf-%s' % v,
        'subnav': 'voted-no',
        'entries': entries,
        'base_template': 'bsdf_base.html',
        'thumb_template': 'bsdf_wd_thumb_vote.html',
        'v': v,
        'enable_voting': True,
    }, extra_context)

    return render(request, template, context)


@require_POST
def bsdf_wd_vote(request):
    v = 'wd'
    id = request.POST['id']
    score = request.POST['score']
    bsdf_model = get_model('bsdfs', 'ShapeBsdfLabel_' + v)
    bsdf_model.objects.filter(id=id).update(admin_score=score)
    return json_success_response()
