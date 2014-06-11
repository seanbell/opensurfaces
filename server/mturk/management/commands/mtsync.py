"""
.. describe:: ./manage.py mtsync

    Synchronize our local information about HITs and assignments with the
    Amazon database.

    This will mark the local copy of HITs as disposed (``hit_status='D'``) if
    they do not exist on Amazon's servers, and it will disable any HITs on
    Amazon if they are not found locally.
"""

from time import sleep

from boto.mturk.connection import MTurkRequestError

from django.conf import settings
from django.core.management.base import BaseCommand

from common.utils import progress_bar
from mturk.utils import get_mturk_connection, extract_mturk_attr
from mturk.models import MtHit, MtAssignment


class Command(BaseCommand):
    args = ''  # '<dir1> <dir2> ...'
    help = 'Syncs HITs with Amazon'

    def handle(self, *args, **options):
        print >>self.stdout, 'MTurk info:'
        for key in dir(settings):
            if key.startswith('MTURK') or 'DEBUG' in key:
                print '  %s: %s' % (key, getattr(settings, key))

        print >>self.stdout, '\nDownloading list of hits...'
        connection = get_mturk_connection()

        # repeatedly try and download list
        while True:
            try:
                all_hits = list(connection.get_all_hits())
                break
            except MTurkRequestError as e:
                print e
                sleep(5)

        # LOCAL
        all_hit_ids = set(extract_mturk_attr(data, 'HITId') for data in all_hits)
        print >>self.stdout, '\nSyncing: local --> Amazon...'
        num_updated = MtHit.objects \
            .filter(sandbox=settings.MTURK_SANDBOX) \
            .exclude(hit_status='D') \
            .exclude(id__in=all_hit_ids) \
            .update(hit_status='D', expired=True)
        if num_updated:
            print 'No remote copy of %s hits -- marked them as disposed' % num_updated

        num_updated = MtAssignment.objects \
            .filter(hit__hit_status='D', status='S') \
            .update(status='A')
        if num_updated:
            print '%s assignments pending with disposed hits -- marked them as approved' % num_updated

        # REMOTE
        for sync_assignments in [False, True]:
            print >>self.stdout, '\nSyncing: Amazon --> local... (sync asst: %s)' % (
                sync_assignments)
            for data in progress_bar(all_hits):
                hit_id = extract_mturk_attr(data, 'HITId')

                try:
                    hit = MtHit.objects.get(id=hit_id)
                    for _ in xrange(5):
                        try:
                            hit.sync_status(
                                data, sync_assignments=sync_assignments)
                            break
                        except MTurkRequestError as e:
                            print e
                            sleep(5)
                except MtHit.DoesNotExist:
                    print 'No local copy of %s -- approving and deleting from Amazon (disabling)' % hit_id
                    try:
                        connection.disable_hit(hit_id)
                    except Exception as exc:
                        print exc

        print >>self.stdout, '\nFetching account balance...'
        print >>self.stdout, 'Account balance:', connection.get_account_balance()
        print >>self.stdout, '\nDone'
