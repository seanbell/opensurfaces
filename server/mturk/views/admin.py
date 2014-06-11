"""
Admin views of mturk data
"""

from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import Http404
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F

from endless_pagination.decorators import page_template
from cacheback.decorators import cacheback

from common.utils import dict_union, dump_queryset_to_static_csv, \
    json_success_response, json_error_response, group_iterable_by_attr

from mturk.models import MtAssignment, Experiment, \
    PendingContent, ExperimentExample
from mturk.aggregate import experiments_as_categories, \
    experiment_slugs, admin_stats_category


@staff_member_required
def admin_experiments(request):
    qset = Experiment.objects.all().select_related('new_hit_settings')
    slugs = group_iterable_by_attr(qset, 'slug')
    slugs = sorted(slugs.iteritems(),
                   key=lambda x: (len(x[1]), x[0]))
    experiments = []
    for s in slugs:
        experiments += s[1]
    experiments.sort(
        key=lambda x: not x.new_hit_settings.auto_add_hits)

    return render(request, "mturk/admin/experiments.html", {
        'nav': 'mturk',
        'subnav': 'experiments',
        'experiments': experiments,
    })


@cacheback(15)
def admin_assignment_csv_url():
    return dump_queryset_to_static_csv(
        MtAssignment.objects.filter(time_ms__isnull=False),
        [
            'time_ms', 'time_load_ms', 'wage',
            ('hit__hit_type__experiment__slug', 'experiment_slug'),
            ('hit__num_contents', 'num_contents'),
        ],
        'mturk-admin-assignment.csv')


@staff_member_required
def admin_stats_table(request, experiment_slug):
    return render(request, "mturk/admin/stats_table.html", {
        'category': admin_stats_category(experiment_slug)
    })


@staff_member_required
def admin_stats(request, experiment_slug='all'):
    return render(request, "mturk/admin/stats.html", {
        'nav': 'mturk-admin',
        'subnav': 'stats',
        'category_slug': experiment_slug,
        'categories': experiments_as_categories(),
        'category': admin_stats_category(experiment_slug),
        'stats_csv_url': admin_assignment_csv_url(),
        'table_template': 'mturk/admin/stats_table.html',
    })


@cacheback(15)
def admin_example_categories():
    ret = filter(lambda x: x['count'] > 0, [
        {'slug': c.slug, 'count': c.examples.count()}
        for c in Experiment.objects.all()
    ])
    ret.sort(key=lambda x: (-x['count'], x['slug']))
    return ret


@staff_member_required
@page_template('grid_page.html')
def admin_example(request, experiment_slug='all',
                  template='mturk/admin/example.html',
                  extra_context=None):

    categories = admin_example_categories()

    entries = ExperimentExample.objects \
        .filter(experiment__slug=experiment_slug) \
        .prefetch_related('content') \
        .order_by('-id')

    # hacky, I know
    if entries and hasattr(entries[0], 'shape_id'):
        entries = list(entries)
        entries.sort(key=lambda x: x.content.shape_id)

    return render(request, template, dict_union({
        'nav': 'mturk-admin',
        'subnav': 'example',
        'entries': entries,
        'categories': categories,
        'category_slug': experiment_slug,
        'entries_per_page': 30,
        'span': 'span3',
        'rowsize': '3',
        'thumb_template_extra': 'mturk/admin/example_thumb_extra.html'
    }, extra_context))


@require_POST
@staff_member_required
def admin_example_ajax(request):
    if 'id' not in request.POST or 'good' not in request.POST:
        return json_error_response(
            'Must have both "id" and "good" in POST params')

    id = request.POST['id']
    good = (request.POST['good'].lower() == 'true')
    updated = ExperimentExample.objects \
        .filter(id=id).update(good=good)

    if updated:
        return json_success_response()
    else:
        return json_error_response('Object (id=%s) not found' % id)


PENDING_CONTENT_FILTERS = {
    'all': {
        'slug': 'All',
        'desc': 'All tracked objects.',
        'filter': {},
    },
    'scheduled': {
        'slug': 'Scheduled',
        'desc': 'These items are part of active HITs.',
        'filter': {'num_outputs_scheduled__gt': 0},
    },
    'unscheduled': {
        'slug': 'Unscheduled',
        'desc': 'These items require more outputs but are not scheduled in any HITs.',
        'filter': {'num_outputs_scheduled__lt':
                   F('num_outputs_max') - F('num_outputs_completed')},
    },
    'incomplete': {
        'slug': 'Incomplete',
        'desc': 'These items require more outputs.',
        'filter': {'num_outputs_completed__lt': F('num_outputs_max')},
    },
    'complete': {
        'slug': 'Complete',
        'desc': 'These items have all of the required outputs.',
        'filter': {'num_outputs_max__gt': 0, 'num_outputs_completed__gte': F('num_outputs_max')},
    },
}

PENDING_CONTENT_FILTERS_LIST = [
    'scheduled', 'unscheduled', 'incomplete', 'complete', 'all',
]


def pending_content_entries(experiment_slug, filter_key):
    if experiment_slug == 'all':
        entries = PendingContent.objects.filter()
    else:
        entries = PendingContent.objects.filter(
            experiment__slug=experiment_slug)

    return entries.filter(**PENDING_CONTENT_FILTERS[filter_key]['filter'])


@cacheback(15)
def admin_pending_content_categories():
    """ Returns a dictionary mapping:
        filter --> category --> {slug, count}
    """
    slugs = experiment_slugs()

    ret = {}
    for filter_key in PENDING_CONTENT_FILTERS_LIST:
        categories = [
            {'slug': slug,
             'count': pending_content_entries(slug, filter_key).count()}
            for slug in slugs
        ]
        categories.append(
            {'slug': 'all',
             'count': pending_content_entries('all', filter_key).count()}
        )
        categories.sort(key=lambda x: (-x['count'], x['slug']))
        ret[filter_key] = categories
    return ret


@page_template('grid_page.html')
@staff_member_required
def admin_pending_content(
    request, experiment_slug='all', filter_key='scheduled',
        template='mturk/admin/pending_content_base.html',
        extra_context=None):

    if filter_key not in PENDING_CONTENT_FILTERS_LIST:
        raise Http404

    categories = admin_pending_content_categories()

    filters = []
    for key in PENDING_CONTENT_FILTERS_LIST:
        count = 0
        for cat in categories[key]:
            if cat['slug'] == experiment_slug:
                count = cat['count']
                break
        else:
            count = categories[key][0]['count']

        filters.append(
            dict_union(
                {'key': key, 'count': count},
                PENDING_CONTENT_FILTERS[key]
            )
        )

    entries = pending_content_entries(experiment_slug, filter_key) \
        .order_by('num_outputs_completed', '-priority')

    return render(request, template, dict_union({
        'nav': 'mturk-admin',
        'subnav': 'pending-content',
        'filters': filters,
        'filter_key': filter_key,
        'categories': categories[filter_key],
        'category_slug': experiment_slug,
        'entries': entries,
        'entries_per_page': 30,
        'span': 'span3',
        'rowsize': '3',
        'thumb_template_extra': 'mturk/admin/pending_content_thumb_extra.html',
    }, extra_context))


@cacheback(15)
def admin_feedback_categories():
    ret = filter(lambda x: x['count'] > 0, [
        {'slug': slug,
         'count': MtAssignment.objects.filter(
             has_feedback=True,
             hit__hit_type__experiment__slug=slug).count()}
        for slug in experiment_slugs()
    ])
    ret.append({
        'slug': 'all',
        'count': MtAssignment.objects.filter(has_feedback=True).count()
    })
    ret.sort(key=lambda x: (-x['count'], x['slug']))
    return ret


@staff_member_required
@page_template('block_page.html')
def admin_feedback(request, experiment_slug='all',
                   template="mturk/admin/feedback.html", extra_context=None):

    assignments = MtAssignment.objects.filter(has_feedback=True)

    if experiment_slug != 'all':
        assignments = assignments.filter(
            hit__hit_type__experiment__slug=experiment_slug)

    if 'worker_id' in request.GET:
        assignments = assignments.filter(
            worker__mturk_worker_id=request.GET['worker_id'])

    entries = assignments \
        .defer('post_data', 'post_meta') \
        .select_related('worker', 'hit__hit_type', 'hit__hit_type__experiment') \
        .order_by('-added')

    return render(request, template, dict_union({
        'nav': 'mturk-admin',
        'subnav': 'feedback',
        'categories': admin_feedback_categories(),
        'category_slug': experiment_slug,
        'entries': entries,
        'entries_per_page': 30,
        'span': 'span9',
        'thumb_template': 'mturk/admin/feedback_entry.html',
    }, extra_context))


SUBMISSION_FILTERS = {
    'all': {
        'slug': 'All',
        'desc': 'All submissions.',
        'filter': {'status__isnull': False},
    },
    'AU': {
        'slug': 'Unblocked',
        'desc': 'All submissions from unblocked users.',
        'filter': {'status__isnull': False, 'worker__blocked': False},
    },
    'S': {
        'slug': 'Pending',
        'desc': 'These assignments are pending (not yet approved/rejected).',
        'filter': {'status': 'S'},
    },
    'A': {
        'slug': 'Approved',
        'desc': 'These assignments were approved.',
        'filter': {'status': 'A'},
    },
    'R': {
        'slug': 'Rejected',
        'desc': 'These assignments were rejected.',
        'filter': {'status': 'R'},
    },
    'HF': {
        'slug': 'Has feedback',
        'desc': 'These assignments have feedback.',
        'filter': {'has_feedback': True},
    },
    'HB': {
        'slug': 'Has bonus',
        'desc': 'These assignments were given a bonus.',
        'filter': {'bonus__gt': 0},
    },
}

SUBMISSION_FILTERS_LIST = ['all', 'AU', 'S', 'A', 'R', 'HF', 'HB']


def submission_entries(experiment_slug, filter_key):
    if experiment_slug == 'all':
        entries = MtAssignment.objects.filter(
            hit__sandbox=False,
            hit__hit_type__experiment__slug=experiment_slug)
    else:
        entries = MtAssignment.objects.filter(
            hit__sandbox=False)

    return entries.filter(**SUBMISSION_FILTERS[filter_key]['filter'])


@cacheback(15)
def admin_submission_categories():
    ret = filter(lambda x: x['count'] > 0, [
        {'slug': slug,
         'count': MtAssignment.objects.filter(
             hit__sandbox=False,
             hit__hit_type__experiment__slug=slug).count()}
        for slug in experiment_slugs()
    ])
    ret.append({
        'slug': 'all',
        'count': MtAssignment.objects.filter(
            hit__sandbox=False,
            status__isnull=False).count()
    })
    ret.sort(key=lambda x: (-x['count'], x['slug']))
    return ret


@staff_member_required
@page_template('block_page.html')
def admin_submission(request, experiment_slug='all', filter_key='all',
                     template="mturk/admin/submission.html", extra_context=None):

    if request.method == 'POST':
        # admin clicked a button in the UI
        try:
            action = request.POST.get['action']
            assignment = MtAssignment.objects.get(
                id=request.POST['assignment_id'])
            if action == 'approve':
                assignment.approve(feedback=request.POST['message'])
                return json_success_response()
            elif action == 'reject':
                assignment.reject(feedback=request.POST['message'])
                return json_success_response()
            elif action == 'auto-approve':
                assignment.experiment_worker().set_auto_approve(
                    message=request.POST['message'])
                return json_success_response()
            elif action == 'block':
                assignment.experiment_worker().block(
                    reason=request.POST['message'],
                    all_tasks=request.POST.get('all_tasks', False),
                    report_to_mturk=request.POST.get('report_to_mturk', False))
                return json_success_response()
            else:
                return json_error_response("Unknown action: '%s'" % action)
        except Exception as e:
            return json_error_response(str(e))

    else:
        extra_filters = {
            'submission_complete': True
        }
        if not settings.MTURK_SANDBOX:
            extra_filters['hit__sandbox'] = False
        if 'worker_id' in request.GET:
            extra_filters['worker__mturk_worker_id'] = request.GET['worker_id']
        if 'hit_id' in request.GET:
            extra_filters['hit_id'] = request.GET['hit_id']

        if filter_key not in SUBMISSION_FILTERS:
            raise Http404
        assignments = MtAssignment.objects.filter(**dict_union(
            extra_filters, SUBMISSION_FILTERS[filter_key]['filter']))

        if experiment_slug != 'all':
            assignments = assignments.filter(
                hit__hit_type__experiment__slug=experiment_slug)

        entries = assignments \
            .defer('post_data', 'post_meta') \
            .order_by('-added') \
            .select_related('worker', 'hit', 'hit__hit_type',
                            'hit__hit_type__experiment') \
            .prefetch_related('submitted_contents__content')

        filters = []
        for key in SUBMISSION_FILTERS_LIST:
            count = 'TODO'
            filters.append(dict_union(
                SUBMISSION_FILTERS[key],
                {'key': key, 'count': count}
            ))

        categories = admin_submission_categories()
        category = None
        for c in categories:
            if c['slug'] == experiment_slug:
                category = c
                break
        else:
            raise Http404

        return render(request, template, dict_union({
            'nav': 'mturk-admin',
            'subnav': 'submission',
            'categories': categories,
            'category_slug': experiment_slug,
            'category': category,
            'filters': filters,
            'filter_key': filter_key,
            'entries': entries,
            'entries_per_page': 1,
            'span': 'span9',
            'thumb_template': 'mturk/admin/submission_entry.html',
        }, extra_context))
