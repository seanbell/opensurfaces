from django.core.management.base import BaseCommand

import json
from collections import OrderedDict
from common.utils import progress_bar
from intrinsic.models import IntrinsicImagesAlgorithm


class Command(BaseCommand):
    args = ''
    help = 'Export the decompositions for the IIW (Intrinsic Images in the Wild) dataset'

    def handle(self, *args, **options):
        algorithms = IntrinsicImagesAlgorithm.objects \
            .filter(iiw_best=True) \
            .order_by('iiw_mean_error') \

        export = [
            OrderedDict([
                ('id', a.id),
                ('slug', a.slug),
                ('citation_html', a.citation.citation_html() if a.citation else None),
                ('iiw_mean_error', a.iiw_mean_error),
                ('iiw_mean_runtime', a.iiw_mean_runtime),
                ('parameters', json.loads(a.parameters)),
                ('intrinsic_images_decompositions', [
                    OrderedDict([
                        ('id', d.id),
                        ('photo_id', d.photo_id),
                        ('runtime', d.runtime),
                        ('mean_error', d.mean_error),
                        ('mean_sparse_error', d.mean_sparse_error),
                        ('mean_dense_error', d.mean_dense_error),
                        ('original_image', d.photo.image_orig.url),
                        ('reflectance_image', d.reflectance_image.url),
                        ('shading_image', d.shading_image.url),
                        ('attribution_name', d.photo.attribution_name
                         if d.photo.attribution_name
                         else (d.photo.flickr_user.display_name if d.photo.flickr_user else None)),
                        ('attribution_url', d.photo.attribution_url if d.photo.attribution_url else d.photo.get_flickr_url()),
                        ('license_name', d.photo.license.name if d.photo.license else None),
                        ('license_url', d.photo.license.url if d.photo.license else None),
                    ])
                    for d in a.intrinsic_images_decompositions
                    .filter(photo__in_iiw_dataset=True)
                    .order_by('photo__id')
                ]),
            ])
            for a in progress_bar(algorithms)
        ]

        print 'Writing json...'
        json.dump(
            obj=export,
            fp=open('intrinsic-decompositions-export.json', 'w'),
            indent=2,
            sort_keys=False)
