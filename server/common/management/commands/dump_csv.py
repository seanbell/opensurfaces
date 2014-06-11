import csv

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode


class Command(BaseCommand):
    args = ''
    help = 'Helper to export CSV data'

    def handle(self, *args, **options):
        outdir = args[0] if len(args) > 0 else '.'
        for ct in ContentType.objects.all():
            model = ct.model_class()
            if ct.app_label in ['photos', 'shapes', 'mturk', 'licenses', 'contenttypes']:
                if ct.model not in ['shapeimagesample', 'pendingcontent']:
                    filename = '%s/%s.%s.csv' % (outdir, ct.app_label, ct.model)
                    print 'Dumping %s...' % filename
                    with open(filename, 'wb') as f:
                        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                        field_names = [f.name for f in model._meta.fields]
                        writer.writerow(field_names)
                        for row in model.objects.all().values_list(*field_names):
                            writer.writerow([smart_unicode(v).encode('utf-8') for v in row])
