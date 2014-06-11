from decimal import Decimal
from clint.textui import progress

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from mturk.utils import get_mturk_connection, extract_mturk_attr
from mturk.models import Experiment, MtHitType, MtHit


class Command(BaseCommand):
    args = ''  # '<dir1> <dir2> ...'
    help = 'Permanently deletes a sandbox experiment'

    def handle(self, *args, **options):
        if not settings.MTURK_SANDBOX or 'sandbox' not in settings.MTURK_HOST:
            print "Permanent delete is only allowed in sandbox (MTURK_SANDBOX) mode"
            return

        experiment = None
        delete_empty = False
        if len(args) == 2:
            task, target = args[0], args[1]
            experiment = Experiment.objects.get(task=task, target=target)
            print 'Finding experiment: task:', task, 'target:', target
        elif len(args) == 1 and args[0] == "all":
            print 'Finding all sandbox experiments'
        elif len(args) == 1 and args[0] == "empty":
            delete_empty = True
            print 'Finding all empty sandbox experiments'
        else:
            print "Usage: <task> <target> or all"
            return

        delete_count = 0
        ignore_count = 0
        missing_count = 0
        connection = get_mturk_connection()
        all_aws_hits = list(connection.get_all_hits())
        to_delete = []

        for aws_hit in progress.bar(all_aws_hits):
            hit_id = extract_mturk_attr(aws_hit, 'HITId')

            try:
                hit = MtHit.objects.get(id=hit_id)
                if not hit.sandbox:
                    ignore_count += 1
                    continue
            except ObjectDoesNotExist:
                print 'Warning: no local copy of HIT', hit_id, '(deleting anyway)'
                connection.disable_hit(hit_id)
                delete_count += 1
                missing_count += 1
                continue

            if not hit: continue

            delete = False
            if delete_empty:
                if hit.contents.count() == 0:
                    to_delete.append(hit)
            else:
                if not experiment or hit.hit_type.experiment == experiment:
                    to_delete.append(hit)

        if len(to_delete) > 0:
            print 'Will delete:'
            for hit in to_delete:
                print '    %s (%s, %s content(s))' % (hit, hit.hit_type.experiment, hit.contents.count())

            if raw_input('Okay? [y/n]: ').lower() != 'y':
                print 'exiting'
                return

            print 'Deleting...'
            with transaction.atomic():
                for hit in progress.bar(to_delete):
                    try:
                        connection.disable_hit(hit.id)
                    except Exception as e:
                        print 'Problem deleting: %s' % e
                    hit.delete()
                    delete_count += 1
        else:
            print 'No HITs to delete'

        if experiment:
            local = MtHit.objects.filter(sandbox=True, hit_type__experiment=experiment)
        else:
            local = MtHit.objects.filter(sandbox=True)

        local_count = local.count()
        local.delete()

        print 'Deleted %d sandbox HITs' % delete_count
        if ignore_count > 0:
            print 'Note: ignored %d non-sandbox HITs' % ignore_count
        if missing_count > 0:
            print 'Note: deleted %d HITs missing from local database' % ignore_count
        if local_count > 0:
            print 'Note: deleted local %d HITs missing from AWS database' % ignore_count

