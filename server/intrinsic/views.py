from django.shortcuts import render, get_object_or_404

from django.http import Http404
from endless_pagination.decorators import page_template

from common.utils import dict_union
from photos.models import Photo
from photos.views import photo_scene_categories
from .models import IntrinsicPointComparison, IntrinsicImagesDecomposition, \
    IntrinsicImagesAlgorithm


def intrinsic_splash(request):
    decompositions = IntrinsicImagesDecomposition.objects.filter(
        algorithm_id=1141,
        #photo_id__in=[105536, 61220, 97532, 116625, 95686, 114977, 35668, 82623]
        photo_id__in=[82623, 35668, 116625],
    ).order_by('photo__num_intrinsic_comparisons')

    decomposition0 = IntrinsicImagesDecomposition.objects.get(algorithm_id=1141, photo_id=105536)

    return render(request, "intrinsic/splash.html", {
        'iiw': True,
        'decompositions': decompositions,
        'decomposition0': decomposition0,
    })


@page_template('block_page.html')
def intrinsic_photo_all(
        request,
        category_id='all',
        filter_key='all',
        template="intrinsic/photo_all.html",
        extra_context=None):

    """ View judgements in images with each image taking up a block and the
    list of photo categories on the left """

    entries = Photo.objects.all()
    if category_id != 'all':
        category_id = int(category_id)
        entries = entries.filter(scene_category_id=category_id)

    entries = entries.filter(in_iiw_dataset=True) \
        .order_by('-num_intrinsic_comparisons') \
        .select_related(
            'intrinsic_comparisons',
            'intrinsic_comparisons__points',
            'intrinsic_points',
            'intrinsic_points__photo')

    context = {
        'iiw': True,
        'nav': 'browse/intrinsic-photo-all',
        'entries': entries,
        'category_id': category_id,
        'filter_key': 'all',
        'url_name': 'intrinsic-photo-all',
        'thumb_template': 'intrinsic/photo_entry.html',
        'span': 'span12',
        'entries_per_page': 4,
    }
    context.update(photo_scene_categories(in_iiw_dataset=True))
    context.update(extra_context)
    return render(request, template, context)


def intrinsic_comparison_detail(
        request, pk, template='intrinsic/comparison_detail.html'):

    entry = get_object_or_404(IntrinsicPointComparison, id=pk)
    context = {
        'iiw': True,
        'nav': 'browse/intrinsic-photo-all',
        'entry': entry,
    }
    return render(request, template, context)


def intrinsic_algorithm_all(
        request, template='intrinsic/algorithm_all.html'):

    entries = IntrinsicImagesDecomposition.objects \
        .filter(photo_id=35668, algorithm__iiw_best=True) \
        .select_related('algorithm', 'photo') \
        .order_by('algorithm__iiw_mean_error')

    num_photos = Photo.objects \
        .filter(in_iiw_dataset=True).count()

    context = {
        'iiw': True,
        'nav': 'browse/intrinsic-algorithm-all',
        'entries': entries,
        'num_photos': num_photos,
    }
    return render(request, template, context)


@page_template('block_page.html')
def intrinsic_decomposition_by_algorithm(
        request,
        algorithm_id=None,
        order_by='mean_error',
        template='intrinsic/decomposition_by_algorithm.html',
        extra_context=None):

    entries = IntrinsicImagesDecomposition.objects
    if algorithm_id:
        algorithm = get_object_or_404(IntrinsicImagesAlgorithm, id=algorithm_id)
        entries = entries.filter(algorithm_id=algorithm_id)
    else:
        algorithm = None
        entries = entries.all()

    entries = entries \
        .filter(photo__in_iiw_dataset=True) \
        .select_related('algorithm') \

    if order_by.endswith('mean_error'):
        entries = entries.order_by(order_by, '-runtime')
    elif order_by.endswith('runtime'):
        entries = entries.order_by(order_by, 'mean_error')
    elif order_by.endswith('photo__num_intrinsic_comparisons'):
        entries = entries.order_by(order_by, 'mean_error')
    else:
        raise Http404

    num_photos = Photo.objects \
        .filter(in_iiw_dataset=True).count()

    context = dict_union({
        'iiw': True,
        'nav': 'browse/intrinsic-decomposition',
        'entries': entries,
        'algorithm': algorithm,
        'thumb_template': 'intrinsic/decomposition_image.html',
        'span': 'span12',
        'entries_per_page': 8,
        'num_photos': num_photos,
        'order_by': order_by
    }, extra_context)

    return render(request, template, context)


#@staff_member_required
#def intrinsic_algorithm_summary(
        #request, template='intrinsic/algorithm_summary.html'):
    #context = {'nav': 'browse/intrnsic'}
    #agg = aggregate_algorithms()
    #if agg:
        #context.update(agg)
    #else:
        #context.update({
            #'rows': [],
            #'num_photo_ids': 0,
            #'num_algorithms': 0,
        #})
    #return render(request, template, context)


#@cacheback(300)
#def aggregate_algorithms(show_progress=False):
    #from intrinsic.evaluation import algorithm_ranks, \
        #completed_photo_ids, completed_algorithm_ids

    #if show_progress:
        #print 'getting completed algorithm ids...'
    #algorithm_ids = completed_algorithm_ids(min_photos=100)
    #algorithms = IntrinsicImagesAlgorithm.objects.in_bulk(algorithm_ids).values()

    #if show_progress:
        #print 'getting photo ids...'
    #photo_ids = completed_photo_ids(algorithm_ids)

    #if show_progress:
        #print 'fetching values...'

    #all_values = IntrinsicImagesDecomposition.objects \
        #.filter(algorithm_id__in=algorithm_ids,
                #mean_sum_error__isnull=False) \
        #.values('photo_id', 'algorithm_id', 'mean_sum_error',
                #'mean_eq_error', 'mean_neq_error', 'runtime')

    ## hash for fast lookup
    #photo_ids = set(photo_ids)
    #algorithm_ids = set(algorithm_ids)

    #if show_progress:
        #print 'filtering by photo...'
    #all_values = [v for v in all_values if v['photo_id'] in photo_ids]

    #if show_progress:
        #print 'computing ranks...'
    #ranks_sum = algorithm_ranks(
        #algorithm_ids, all_values, show_progress=show_progress)

    ## prepare each alg
    #if show_progress:
        #print 'aggregating errors...'
    #f = lambda L: [x for x in L if x is not None]
    #rows = []
    #iterator = progress_bar(algorithms) if show_progress else algorithms
    #for alg in iterator:
        #values = [v for v in all_values
                  #if (v['photo_id'] in photo_ids and
                      #v['algorithm_id'] in algorithm_ids)]

        #eq = f([x['mean_eq_error'] for x in values])
        #neq = f([x['mean_neq_error'] for x in values])
        #s = f([0.5 * x['mean_sum_error'] for x in values])
        #rt = f([x['runtime'] for x in values])

        #rows.append({
            #'algorithm': alg,
            #'rank_sum_mean': np.mean(ranks_sum[alg.id]),
            #'rank_sum_median': np.median(ranks_sum[alg.id]),
            #'rank_sum_std': np.std(ranks_sum[alg.id]),
            #'neq_mean': np.mean(neq),
            #'neq_median': np.median(neq),
            #'neq_std': np.std(neq),
            #'eq_mean': np.mean(eq),
            #'eq_median': np.median(eq),
            #'eq_std': np.std(eq),
            #'mean_mean': np.mean(s),
            #'mean_median': np.median(s),
            #'mean_std': np.std(s),
            #'runtime_mean': np.mean(rt),
            #'runtime_std': np.std(rt),
        #})
    #rows.sort(key=lambda x: x['rank_sum_mean'])

    #return {
        #'rows': rows,
        #'num_photo_ids': len(photo_ids),
        #'num_algorithms': len(algorithm_ids),
    #}
