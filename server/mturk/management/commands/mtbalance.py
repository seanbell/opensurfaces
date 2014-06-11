"""
.. describe:: ./manage.py mtbalance

    Print the current account balance.

"""

from django.conf import settings
from django.core.management.base import BaseCommand

from mturk.utils import get_mturk_connection


class Command(BaseCommand):
    args = ''  # '<dir1> <dir2> ...'
    help = 'Prints the current balance'

    def handle(self, *args, **options):
        print >>self.stdout, 'MTurk info:'
        for key in dir(settings):
            if key.startswith('MTURK') or 'DEBUG' in key:
                print '  %s: %s' % (key, getattr(settings, key))

        print '\nFetching account balance...'
        print 'Account balance:', get_mturk_connection().get_account_balance()
