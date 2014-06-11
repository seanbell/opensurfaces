"""
.. describe:: ./manage.py mtexpire '<regex>'

    Expire all experiments whose ``slug`` matches a regex.  When a HIT is expired,
    any current workers may finish, but no new workers may start the HIT.

    This script expires in decreasing order of pay.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from mturk.models import MtHit, Experiment
from common.utils import progress_bar


class Command(BaseCommand):
    args = ''
    help = 'Exprire experiments that meet a regex'

    def handle(self, *args, **options):
        if len(args) == 1:
            regex = args[0]
            experiments = Experiment.objects.filter(slug__regex=regex)
            if experiments.count() == Experiment.objects.all().count():
                print 'Expiring all experiments'
            else:
                print 'Expiring: %s' % experiments.values_list('slug', flat=True)
        else:
            print "Usage: ./manage.py mtexpire '<regex>'"
            return

        print 'MTURK HOST:', settings.MTURK_HOST
        hits = MtHit.objects.filter(
            expired=False, sandbox=settings.MTURK_SANDBOX,
        )
        if regex != '.*':
            hits = hits.filter(
                hit_type__experiment__slug__regex=regex
            )

        # Expire by highest paying first, just in case you accidentally added
        # HITs that pay $100 and want to expire it quickly.  We have to fetch
        # all the items anyway, so might as well do the sort in python.
        hits = sorted(hits.select_related('hit_type'),
                      key=lambda x: x.hit_type.reward * x.num_assignments_available,
                      reverse=True)

        count = 0
        try:
            for hit in progress_bar(hits):
                print ''
                try:
                    if hit.expire():
                        count += 1
                except Exception as exc:
                    print exc
        finally:
            print 'Expired %d hits' % count
