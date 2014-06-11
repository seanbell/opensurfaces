"""
.. describe:: ./manage.py mtapprove_loop '<regex>'

    Instantly approve all submissions, the moment they arrive.  In a loop, this
    script finds all experiments whose ``slug`` matches the given regex and
    approves all submitted assignments.

    I suggest running this script whenever you have an experiment that has
    sentinel objects (secret items with known answers), since workers greatly
    appreciate speedy approval.
"""

import time
from django.conf import settings
from django.core.management.base import BaseCommand

from common.utils import progress_bar
from mturk.models import MtAssignment


class Command(BaseCommand):
    args = ''
    help = 'Repeatedly approve submissions as they come in'

    def handle(self, *args, **options):
        if len(args) == 1:
            regex = args[0]
        else:
            print "Usage: ./manage.py mtapprove_loop '<regex>'"
            return

        # it takes a little while for MTurk to let you approve an assignment
        # after submission
        sleep_time = 5

        while True:
            assignments = MtAssignment.objects \
                .filter(hit__sandbox=settings.MTURK_SANDBOX, status='S')

            if regex != '.*':
                assignments = assignments.filter(
                    hit__hit_type__experiment__slug__regex=regex)

            c = 0
            for a in progress_bar(assignments):
                try:
                    a.approve(feedback="Thank you!")
                    c += 1
                except Exception as e:
                    if 'This operation can be called with a status of: null' in str(e):
                        print '    (MTurk not ready for approval yet)'
                    else:
                        print e

            if c > 0:
                sleep_time = max(sleep_time // 2, 5)
            else:
                sleep_time = min(sleep_time * 2, 60)

            print "approved %s assignments; sleep %s seconds..." % (c, sleep_time)
            time.sleep(sleep_time)
