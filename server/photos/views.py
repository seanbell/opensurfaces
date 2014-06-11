import json

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from cacheback.decorators import cacheback
from endless_pagination.decorators import page_template
from django.http import Http404

from common.utils import dict_union, prepare_votes_bar, \
    json_response, json_success_response
from photos.models import Photo, PhotoSceneCategory

# different ways photos can be filtered
PHOTO_FILTERS = {
    'all': {
        'name': 'Raw input',
        'filter': Photo.DEFAULT_FILTERS
    },

    'wb': {
        'name': 'Whitebalanced (WB)',
        'filter': dict_union(
            Photo.DEFAULT_FILTERS, {
                'whitebalanced': True,
            })
    },

    'nwb': {
        'name': 'Not WB',
        'filter': dict_union(
            Photo.DEFAULT_FILTERS, {
                'whitebalanced': False,
            })
    },

    'vp': {
        'name': 'Has vanishing points',
        'filter': dict_union(
            Photo.DEFAULT_FILTERS, {
                'vanishing_length__isnull': False,
            })
    },

    'ls': {
        'name': 'Varying lighting',
        'filter': {
            'light_stack__isnull': False,
        }
    },

    'syn': {
        'name': 'Synthetic',
        'filter': {
            'intrinsic_synthetic__multilayer_exr__isnull': False
        }
    },

    'ia': {
        'name': 'Has intrinsic judgements',
        'filter': {
            'in_iiw_dataset': True,
        }
    },

    'id': {
        'name': 'Has dense intrinsic judgements',
        'filter': {
            'in_iiw_dataset': True,
            'in_iiw_dense_dataset': True,
        }
    },
}
# display order
PHOTO_FILTER_KEYS = ['wb', 'nwb', 'vp', 'ls', 'ia', 'id', 'syn', 'all']


def photo_by_category_entries(category_id, filter_key):
    """ Returns queryset for each filter """

    photo_filter = PHOTO_FILTERS[filter_key]['filter']
    if category_id != 'all':
        photo_filter = dict_union(photo_filter, {
            'scene_category_id': category_id
        })
    return Photo.objects.filter(**photo_filter)


@cacheback(3600)
def photo_scene_categories(**filters):
    """ Returns the category list along with photo counts """
    categories = [
        {'id': c.id, 'name': c.name, 'count': c.photo_count(**filters)}
        for c in PhotoSceneCategory.objects.all()
    ]
    categories = filter(lambda x: x['count'], categories)
    categories.sort(key=lambda x: x['count'], reverse=True)

    categories_all = [
        {'id': 'all', 'name': 'all', 'count': Photo.objects.filter(
            **Photo.DEFAULT_FILTERS
        ).filter(**filters).count()}
    ]

    return {
        'categories': categories,
        'categories_all': categories_all
    }


@cacheback(300)
def photo_by_category_filters(category_id):
    """ Returns the list of filters extended with the photo count """
    ret = []
    for k in PHOTO_FILTER_KEYS:
        ret.append(dict_union({
            'key': k,
            'count': photo_by_category_entries(category_id, k).count(),
        }, PHOTO_FILTERS[k]))
    return ret


@page_template('grid_page.html')
def photo_by_category(request, category_id='all', filter_key='wb',
                      template='photos/by_category.html',
                      extra_context=None):

    """ List of photos, filtered by a scene and optional extra ``filter_key`` """

    if filter_key not in PHOTO_FILTERS:
        raise Http404

    if category_id != 'all':
        category_id = int(category_id)

    entries = photo_by_category_entries(category_id, filter_key)

    query_filter = {}
    for k, v in request.GET.iteritems():
        if k == u'page' or k == u'querystring_key':
            continue
        elif k == u'publishable':
            query_filter['license__publishable'] = True
        else:
            query_filter[k] = v
    if query_filter:
        entries = entries.filter(**query_filter)

    if filter_key == 'vp':
        entries = entries.order_by('-vanishing_length')
    elif filter_key == 'ic':
        entries = entries.order_by('-num_intrinsic_comparisons')
    else:
        if filter_key == 'all':
            entries = entries.order_by('-added')
        else:
            entries = entries.order_by('-num_vertices', '-scene_category_correct_score')

    context = dict_union({
        'nav': 'browse/photo',
        'subnav': 'by-category',
        'filter_key': filter_key,
        'category_id': category_id,
        'filters': photo_by_category_filters(category_id),
        'url_name': 'photo-by-category',
        'entries': entries,
        'entries_per_page': 30,
        'span': 'span3',
        'rowsize': '3',
        'thumb_template': 'photos/thumb.html',
    }, extra_context)

    context.update(photo_scene_categories())
    return render(request, template, context)


def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)

    votes = [
        prepare_votes_bar(
            photo, 'scene_qualities', 'scene_category_correct',
            'correct', 'Scene label correct'),
        prepare_votes_bar(
            photo, 'whitebalances', 'whitebalanced',
            'whitebalanced', 'Whitebalance'),
    ]

    try:
        intrinsic_synthetic = photo.intrinsic_synthetic
    except ObjectDoesNotExist:
        intrinsic_synthetic = None

    # sections on the page
    nav_section_keys = [
        ("photo", 'Photo'),
        ("shapes", 'Material segmentations'),
        ("vanishing", 'Vanishing points'),
        ("whitebalance", 'Whitebalance'),
        ("intrinsic_synthetic", 'Synthetic Rendering') if intrinsic_synthetic else None,
        ("intrinsic_judgements", 'Reflectance Judgements'),
        ("intrinsic_decompositions", 'Intrinsic Image Decompositions'),
    ]
    nav_sections = [
        {
            'key': t[0],
            'name': t[1],
            'template': 'photos/detail/%s.html' % t[0],
        }
        for t in nav_section_keys if t
    ]

    return render(request, 'photos/detail.html', {
        'nav': 'browse/photo',
        'photo': photo,
        'votes': votes,
        'intrinsic_synthetic': intrinsic_synthetic,
        'nav_sections': nav_sections,
    })


@ensure_csrf_cookie
@staff_member_required
def photo_curate(request, template='photos/curate.html'):
    if request.method == 'POST':
        if request.POST['action'] == 'button':
            photo_id = request.POST['photo_id']
            attr = request.POST['attr']
            Photo.objects.filter(id=photo_id).update(
                **{attr: request.POST['val'].lower() == u'true'}
            )
            val = Photo.objects.filter(id=photo_id) \
                .values_list(attr, flat=True)[0]
            return json_response({
                'photo_id': photo_id,
                'attr': attr,
                'val': val
            })
        elif request.POST['action'] == 'done':
            items = json.loads(request.POST['items'])
            for item in items:
                print item
                Photo.objects.filter(id=item['photo_id']).update(
                    **item['updates']
                )
            return json_success_response()
        else:
            raise Http404
    else:
        entries = Photo.objects \
            .filter(scene_category_correct=True) \
            .filter(
                Q(inappropriate__isnull=True) |
                Q(nonperspective__isnull=True) |
                Q(stylized__isnull=True) |
                Q(rotated__isnull=True)) \
            .order_by('-num_vertices', 'scene_category_correct_score')

        count = entries.count()
        entries = list(entries[:400])
        entries.sort(key=lambda x: x.aspect_ratio)

        return render(request, template, {
            'nav': 'browse/photo',
            'count': count,
            'entries': entries,
        })
