import glob
import time
import timeit
from django.core.management.base import BaseCommand

from intrinsic.tasks import import_ec2_task


class Command(BaseCommand):
    args = ''
    help = 'Import image algorithms run on ec2'

    def handle(self, *args, **options):
        indir = '/vol/completed-tasks'
        scheduled_fnames = {}
        sleep_time = 2

        total_count = None
        start_time = None
        first = True

        while True:
            files = glob.glob("%s/*.pickle" % indir)

            c = 0
            for fname in files:
                if fname in scheduled_fnames:
                    scheduled_fnames[fname] -= sleep_time
                else:
                    scheduled_fnames[fname] = 0

                if scheduled_fnames[fname] <= 0:
                    import_ec2_task.delay(fname)
                    scheduled_fnames[fname] = 3600
                    c += 1

            # ignore the first time
            if first:
                total_count = 0
                start_time = timeit.default_timer()
                rate = "N/A"
                first = False
            else:
                total_count += c
                time_elapsed = max(timeit.default_timer() - start_time, 1e-3)
                rate = "%.3f" % (float(total_count) / time_elapsed)

            if c > 0:
                sleep_time = max(sleep_time // 2, 2)
            else:
                sleep_time = min(sleep_time * 2, 3600)
            time.sleep(sleep_time)

            print "%s new files (average %s files/s); sleep for %s seconds..." % (
                c, rate, sleep_time)
