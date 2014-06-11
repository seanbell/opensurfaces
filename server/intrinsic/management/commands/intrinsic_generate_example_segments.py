import os
from django.core.management.base import BaseCommand


from photos.models import Photo
from intrinsic.models import IntrinsicImagesDecomposition

from imagekit.utils import open_image
from shapes.utils import mask_complex_polygon
from common.utils import progress_bar


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):
        photos = Photo.objects.filter(id__in=[95686, 97532, 116625, 85877, 69122, 104870])
        for p in photos:
            decomp = IntrinsicImagesDecomposition.objects.get(photo_id=p.id, algorithm_id=1141)
            img_i = p.open_image(width='orig')
            img_r = open_image(decomp.reflectance_image)
            img_s = open_image(decomp.shading_image)

            if not os.path.exists('example-intrinsic-segments/%s' % p.id):
                os.makedirs('example-intrinsic-segments/%s' % p.id)

            img_i.save('example-intrinsic-segments/%s/image.jpg' % p.id)
            img_r.save('example-intrinsic-segments/%s/reflectance.png' % p.id)
            img_s.save('example-intrinsic-segments/%s/shading.png' % p.id)

            for s in progress_bar(p.material_shapes.all()):
                mask_complex_polygon(img_i, s.vertices, s.triangles)[0].save('example-intrinsic-segments/%s/shape-%s-image.png' % (p.id, s.id))
                mask_complex_polygon(img_r, s.vertices, s.triangles)[0].save('example-intrinsic-segments/%s/shape-%s-reflectance.png' % (p.id, s.id))
                mask_complex_polygon(img_s, s.vertices, s.triangles)[0].save('example-intrinsic-segments/%s/shape-%s-shading.png' % (p.id, s.id))
