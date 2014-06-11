"""
Aggregation utilities used by view functions
"""

import datetime
from django.http import Http404
from django.db.models import Sum, Count

from cacheback.decorators import cacheback

from common.utils import dict_union, all_aggregations, scale_dict_values
from mturk.models import MtHit, MtAssignment, Experiment


@cacheback(300)
def experiment_slugs():
    return sorted(
        Experiment.objects.all().order_by()
        .values_list('slug', flat=True).distinct()
    )


@cacheback(300)
def experiments_as_categories():
    l = ['all'] + experiment_slugs()
    return [{'slug': s} for s in l]


@cacheback(300)
def aggregate_experiment_all():
    """ Aggregate information for each experiment (by slug), as well as across
    all experiments.  Returns None on cache miss. """

    experiments = {}

    hits = MtHit.objects.filter(sandbox=False)
    aggregate = aggregate_hits(hits)
    aggregate['slug'] = 'all'
    experiments['all'] = aggregate

    for slug in experiment_slugs():
        hits = MtHit.objects.filter(
            hit_type__experiment__slug=slug, sandbox=False)
        aggregate = aggregate_hits(hits)
        aggregate['slug'] = slug
        experiments[slug] = aggregate

    return experiments


def admin_stats_category(experiment_slug):
    aggregates = aggregate_experiment_all()
    if aggregates:
        if experiment_slug in aggregates:
            return aggregates[experiment_slug]
        else:
            raise Http404
    else:
        return None


def aggregate_hits(hits):
    """ Aggregate information for a set of HITs and assignments """
    assts = MtAssignment.objects.filter(hit__in=hits)
    return {
        'now': datetime.datetime.now(),
        'counts': {
            'hit': [
                ('Active', hits.filter(
                    expired=False, all_submitted_assignments=False).count()),
                ('Partial', hits.filter(
                    expired=False, all_submitted_assignments=False,
                    any_submitted_assignments=True).count()),
                ('Complete', hits.filter(
                    all_submitted_assignments=True).count()),
                ('Expired', hits.filter(expired=True).count()),
                #('Disposed', hits.filter(hit_status='D').count()),
            ], 'asst': [
                ('To review', assts.filter(status='S').count()),
                ('Approved', assts.filter(status='A').count()),
                ('Rejected', assts.filter(status='R').count()),
                ('Rejected manually', assts.filter(
                    manually_rejected=True).count()),
                ('Has feedback', assts.filter(has_feedback=True).count()),
            ], 'other': [
                ('Unique workers', assts.filter(status__isnull=False).aggregate(
                    count=Count('worker', distinct=True))['count']),
                ('WebGL compatible', hits.aggregate(
                    sum=Sum('compatible_count'))['sum']),
                ('WebGL incompatible', hits.aggregate(
                    sum=Sum('incompatible_count'))['sum']),
            ]
        }, 'aggregations': [
            ('Time', dict_union(
                {'unit': 's'}, scale_dict_values(
                    all_aggregations(assts, 'time_ms'),
                    scale=0.001, exclude=['count']))),
            ('Active Time', dict_union(
                {'unit': 's'}, scale_dict_values(
                    all_aggregations(assts, 'time_active_ms'),
                    scale=0.001, exclude=['count']))),
            ('Screen Width', dict_union(
                {'unit': ''}, all_aggregations(assts, 'screen_width'))),
            ('Screen Height', dict_union(
                {'unit': ''}, all_aggregations(assts, 'screen_height'))),
            ('Reward', dict_union(
                {'unit': '$'}, all_aggregations(
                    assts.filter(status='A'), 'hit__hit_type__reward'))),
            ('Wage', dict_union(
                {'unit': '$/hr'}, all_aggregations(
                    assts.filter(status='A'), 'wage'))),
            ('Bonus', dict_union(
                {'unit': '$'}, all_aggregations(
                    assts.filter(bonus__gt=0), 'bonus'))),
            ('Feedback bonus', dict_union(
                {'unit': '$'}, all_aggregations(
                    assts.filter(feedback_bonus_given=True),
                    'hit__hit_type__feedback_bonus'))),
            ('Num contents', dict_union(
                {'unit': ''}, all_aggregations(assts, 'hit__num_contents'))),
        ],
    }
