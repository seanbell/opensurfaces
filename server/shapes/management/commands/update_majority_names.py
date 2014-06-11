from clint.textui import progress

from django.core.management.base import BaseCommand

from shapes.models import MaterialShapeNameLabel, ShapeSubstanceLabel
from shapes.tasks import fill_in_bbox_task
from django.db import transaction


class Command(BaseCommand):
    args = ''
    help = 'Helper to recompute the majority label for shapes'

    def handle(self, *args, **options):
        with transaction.atomic():
            for label in progress.bar(ShapeSubstanceLabel.objects.all()):
                new_hit_settings = label.mturk_assignment.hit.hit_type.experiment.new_hit_settings
                shape = label.shape
                substance = label.substance
                if (shape.substances.filter(substance=substance).count() >=
                        new_hit_settings.min_assignment_consensus):
                    shape.substance = substance
                    shape.update_entropy(save=False)
                    shape.save()

        with transaction.atomic():
            for label in progress.bar(MaterialShapeNameLabel.objects.all()):
                new_hit_settings = label.mturk_assignment.hit.hit_type.experiment.new_hit_settings
                shape = label.shape
                name = label.name
                if (shape.names.filter(name=name).count() >=
                        new_hit_settings.min_assignment_consensus):
                    shape.name = name
                    shape.update_entropy(save=False)
                    shape.save()

