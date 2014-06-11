from django.core.management.base import BaseCommand

from licenses.models import License
from photos.models import Photo


class Command(BaseCommand):
    args = ''
    help = 'Fix intrinsic images licenses'

    def handle(self, *args, **options):

        all_rights_reserved = License.objects.get(
            name='All Rights Reserved')
        cc_generic = License.objects.get(
            url='http://creativecommons.org/licenses/by/2.0/')

        Photo.objects.filter(id__in=[118508, 118507]) \
            .update(license=all_rights_reserved,
                    attribution_name="Michael Kelley",
                    attribution_url="http://www.mpkelley.com/")
        Photo.objects.filter(id__in=[118509, 118510, 118511, 118512]) \
            .update(license=cc_generic,
                    attribution_name="Sean Bell",
                    attribution_url="http://www.seanbell.ca/")
        Photo.objects.filter(id__in=[118513, 118514]) \
            .update(license=cc_generic,
                    attribution_name="Ivaylo Boyadzhiev and Sylvain Paris",
                    attribution_url="http://www.cs.cornell.edu/~iboy/")
        Photo.objects.filter(id__in=[118516, 118515, 118517]) \
            .update(license=cc_generic,
                    attribution_name="Sylvain Paris",
                    attribution_url="http://people.csail.mit.edu/sparis/")
