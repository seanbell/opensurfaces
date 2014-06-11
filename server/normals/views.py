import json

from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import ensure_csrf_cookie

from endless_pagination.decorators import page_template

from common.utils import dict_union, prepare_votes_bar, \
    json_success_response, json_error_response
from normals.models import ShapeRectifiedNormalLabel


def rectified_normal_detail(request, pk):
    entry = get_object_or_404(ShapeRectifiedNormalLabel, pk=pk)
    votes = [
        prepare_votes_bar(entry, 'qualities', 'correct', 'correct', 'Quality'),
    ]

    data = {
        'nav': 'browse/rectified-normal',
        'entry': entry,
        'votes': votes,
    }
    return render(request, 'rectified_normal_detail.html', data)


@page_template('grid3_page.html')
def rectified_normal_all(request, template='endless_list.html',
                         extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects.all().order_by('-id')

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'all',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb.html',
        'header': 'All submissions',
        'header_small': 'sorted by submission time',
        #'enable_voting': False,
    }, extra_context)

    return render(request, template, context)


@page_template('grid3_page.html')
def rectified_normal_good(request, template='endless_list.html',
                          extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(shape__planar=True, correct=True, correct_score__isnull=False) \
        .order_by('-correct_score')
        #.filter(admin_score__gt=0, shape__synthetic=False) \
        #.order_by('-admin_score', '-shape__pixel_area')

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'good',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb.html',
        'header': 'High quality submissions'
        #'header_sub': 'These submissions were voted as high quality.'
        #'enable_voting': False,
    }, extra_context)

    return render(request, template, context)


@page_template('grid3_page.html')
def rectified_normal_bad(request, template='endless_list.html',
                         extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(shape__planar=True, correct=False, correct_score__isnull=False) \
        .order_by('correct_score')
        #.filter(admin_score__lt=0, shape__synthetic=False) \
        #.order_by('admin_score', 'shape__num_vertices')

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'bad',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb.html',
        'header': 'Low quality submissions',
        'header_small': 'sorted by quality',
        #'enable_voting': False,
    }, extra_context)

    return render(request, template, context)


@page_template('grid3_page.html')
def rectified_normal_auto(request, template='endless_list.html',
                          extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(shape__planar=True, shape__correct=True, automatic=True) \
        .order_by('-shape__num_vertices')

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'auto',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb.html',
        'header': 'Automatically rectified shapes',
        'header_small': 'using vanishing points',
    }, extra_context)

    return render(request, template, context)


@page_template('grid3_page.html')
def rectified_normal_best(request, template='endless_list.html',
                          extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(shape__photo__inappropriate=False,
                shape__correct=True, shape__planar=True,
                shape__rectified_normal_id=F('id')) \

    if 'by-id' in request.GET:
        header_small = 'sorted by id'
        entries = entries.order_by('-id')
    else:
        header_small = 'sorted by complexity'
        entries = entries.order_by('-shape__num_vertices')

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'best',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb.html',
        'header': 'High quality submissions',
        'header_small': header_small,
    }, extra_context)

    return render(request, template, context)


@staff_member_required
@page_template('grid3_page.html')
def rectified_normal_curate(
        request, template='endless_list_curate.html', extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(shape__planar=True, correct=True) \
        .order_by('-shape__num_vertices')

    if 'publishable' in request.GET:
        entries = entries.filter(shape__photo__license__publishable=True)

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'curate',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb.html',
        'header': 'Curate rectified textures',
        'curate_post_url': reverse('rectified-normal-curate-post'),
        'curate': True
    }, extra_context)

    return render(request, template, context)


@require_POST
@staff_member_required
def rectified_normal_curate_post(request):
    if request.POST['model'] != "shapes/shaperectifiednormallabel":
        return json_error_response("invalid model")
    normal = ShapeRectifiedNormalLabel.objects.get(id=request.POST['id'])
    normal.quality_method = 'A'
    normal.correct = not normal.correct
    normal.save()
    normal.shape.update_entropy(save=True)
    return HttpResponse(
        json.dumps({'selected': not normal.correct}),
        mimetype='application/json')


@ensure_csrf_cookie
@page_template('grid3_page.html')
def rectified_normal_voted_none(request, template='endless_list.html',
                                extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(admin_score=0, time_ms__gt=500, shape__dominant_delta__isnull=False) \
        .order_by('-shape__synthetic', '?')

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'vote',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb_vote.html',
        'enable_voting': True,
    }, extra_context)

    return render(request, template, context)


@ensure_csrf_cookie
@page_template('grid3_page.html')
def rectified_normal_voted_yes(request, template='endless_list.html',
                               extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(admin_score__gt=0) \
        .order_by('-admin_score', '-shape__pixel_area')

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'voted-yes',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb_vote.html',
        'enable_voting': True,
    }, extra_context)

    return render(request, template, context)


@ensure_csrf_cookie
@page_template('grid3_page.html')
def rectified_normal_voted_no(request, template='endless_list.html',
                              extra_context=None):

    entries = ShapeRectifiedNormalLabel.objects \
        .filter(admin_score__lt=0) \
        .order_by('admin_score', '-shape__pixel_area')

    context = dict_union({
        'nav': 'browse/rectified-normal', 'subnav': 'voted-no',
        'entries': entries,
        'base_template': 'rectified_normal_base.html',
        'thumb_template': 'rectified_normal_thumb_vote.html',
        'enable_voting': True,
    }, extra_context)

    return render(request, template, context)


@require_POST
def rectified_normal_vote(request):
    id = request.POST['id']
    score = request.POST['score']
    ShapeRectifiedNormalLabel.objects.filter(id=id).update(admin_score=score)
    return json_success_response()
