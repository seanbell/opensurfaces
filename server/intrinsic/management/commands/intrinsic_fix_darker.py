from django.core.management.base import BaseCommand

from common.utils import progress_bar
from colormath.color_objects import RGBColor

from intrinsic.models import IntrinsicPointComparison, \
    IntrinsicPointComparisonResponse


class Command(BaseCommand):
    args = ''
    help = 'Fix the point1_image_darker field'

    def handle(self, *args, **options):
        comparisons = []

        comparisons += IntrinsicPointComparison.objects.all() \
            .filter(point1_image_darker__isnull=True) \
            .values_list('id', 'point1__sRGB', 'point2__sRGB')

        comparisons += IntrinsicPointComparisonResponse.objects.all() \
            .filter(reflectance_eq=False, reflectance_dd__isnull=True) \
            .order_by().distinct('comparison') \
            .values_list('comparison__id', 'comparison__point1__sRGB', 'comparison__point2__sRGB')

        comparisons = list(set(comparisons))

        for (id, sRGB1, sRGB2) in progress_bar(comparisons):
            c1 = RGBColor()
            c1.set_from_rgb_hex(sRGB1)
            l1 = c1.convert_to('lab').lab_l

            c2 = RGBColor()
            c2.set_from_rgb_hex(sRGB2)
            l2 = c2.convert_to('lab').lab_l

            if l1 < l2:
                IntrinsicPointComparison.objects \
                    .filter(id=id).update(point1_image_darker=True)
                IntrinsicPointComparisonResponse.objects \
                    .filter(comparison_id=id, darker="1") \
                    .update(reflectance_eq=False, reflectance_dd=True)
                IntrinsicPointComparisonResponse.objects \
                    .filter(comparison_id=id, darker="2") \
                    .update(reflectance_eq=False, reflectance_dd=False)
            else:
                IntrinsicPointComparison.objects \
                    .filter(id=id).update(point1_image_darker=False)
                IntrinsicPointComparisonResponse.objects \
                    .filter(comparison_id=id, darker="1") \
                    .update(reflectance_eq=False, reflectance_dd=False)
                IntrinsicPointComparisonResponse.objects \
                    .filter(comparison_id=id, darker="2") \
                    .update(reflectance_eq=False, reflectance_dd=True)

            IntrinsicPointComparisonResponse.objects \
                .filter(comparison_id=id, darker="E") \
                .update(reflectance_eq=True, reflectance_dd=None)
