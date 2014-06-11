from optparse import make_option
from clint.textui import progress

from django.core.management.base import BaseCommand

from shapes.models import MaterialShape
from shapes.utils import update_shape_dominant_rgb


class Command(BaseCommand):
    args = ''
    help = 'Helper to fill in a potentially empty field'

    option_list = BaseCommand.option_list + (
        make_option(
            '--skip_completed',
            action='store_true',
            dest='skip_completed',
            default=False,
            help='Skip already completed shapes'),
    )

    def handle(self, *args, **options):
        #with transaction.atomic():
        for shape in progress.bar(MaterialShape.objects.filter()):
            if shape.dominant_rgb0 and options['skip_completed']:
                continue
            update_shape_dominant_rgb(shape, save=True)
