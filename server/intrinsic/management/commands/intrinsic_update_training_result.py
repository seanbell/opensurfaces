from django.core.management.base import BaseCommand

from intrinsic.tasks import intrinsic_update_training_result


class Command(BaseCommand):
    args = ''
    help = 'Update IntrinsicImagesAlgorithmTrainingResult'

    def handle(self, *args, **options):
        intrinsic_update_training_result(show_progress=True)
