from clint.textui import progress

from django.core.management.base import BaseCommand
from django.db.models.loading import cache
from django.db import models
from django.core.files.storage import DefaultStorage
from django.contrib.contenttypes.models import ContentType

from common.tasks import ensure_thumbs_exist_task


class Command(BaseCommand):
    args = ''
    help = 'Transfer all images to S3'

    def handle(self, *args, **options):
        storage = DefaultStorage()

        for model in _get_models(['shapes', 'photos', 'shapes']):
            has_images = False

            # transfer image fields
            for f in model._meta.fields:
                if isinstance(f, models.ImageField):
                    has_images = True
                    if hasattr(storage, 'transfer'):
                        filenames = model.objects.all() \
                            .values_list(f.name, flat=True)
                        print '%s: %s' % (model, f)
                        for filename in progress.bar(filenames):
                            if filename and storage.local.exists(filename):
                                storage.transfer(filename)

            # transfer thumbs
            if has_images:
                print '%s: thumbnails' % model
                ids = model.objects.all().values_list('id', flat=True)
                ct_id = ContentType.objects.get_for_model(model).id
                for id in progress.bar(ids):
                    ensure_thumbs_exist_task.delay(ct_id, id)


def _get_models(apps):
    ret = []
    for app_label in apps or []:
        app = cache.get_app(app_label)
        ret += [m for m in cache.get_models(app)]
    return ret
