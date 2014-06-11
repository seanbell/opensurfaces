from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    args = ''
    help = 'Helper to export CSV data'

    def handle(self, *args, **options):
        outdir = args[0] if len(args) > 0 else '.'

        print '#!/bin/bash'
        print 'set -x'
        print 'mkdir -p %s' % outdir

        for ct in ContentType.objects.all():
            #model = ct.model_class()
            if ct.app_label in ['photos', 'shapes', 'mturk', 'licenses', 'contenttypes']:
                if ct.model not in ['shapeimagesample', 'pendingcontent', 'shapenormallabel', 'shapebsdflabel_mf']:
                    print './manage.py dumpdata --format json --indent 1 %s.%s > %s/%s.%s.json' % (
                        ct.app_label, ct.model, outdir, ct.app_label, ct.model)
