from django.core.management.base import BaseCommand

from shapes.models import ShapeSubstance
from shapes.tasks import save_substance_grid
from normals.tasks import save_texture_grid
from bsdfs.tasks import save_substance_reflectance_grid


class Command(BaseCommand):
    args = ''
    help = 'Takes all images in the database and creates tiny versions of them'

    def handle(self, *args, **options):

        #save_texture_grid('texture-grid', max_qset_size=10000, ncols=100, show_progress=True, category=None)
        #save_texture_grid.delay('texture-grid', max_qset_size=25, show_progress=True, category='Granite')
        #save_texture_grid.delay('texture-grid', max_qset_size=25, show_progress=True, category='Tile')
        #save_texture_grid.delay('texture-grid', max_qset_size=25, show_progress=True, category='Marble')

        for id in ShapeSubstance.objects.all().values_list('id', flat=True):
            save_substance_grid.delay(id, 'substance-grid-new', show_progress=True)

        #save_substance_reflectance_grid(
            #'bsdf-sequence', max_sequence_len=10000, ncols=100, initial_id=None, substance=None, show_progress=True)
        #save_substance_reflectance_grid(
            #'bsdf-sequence', max_sequence_len=25, initial_id=32198, substance="Fabric/cloth", show_progress=True)
        #save_substance_reflectance_grid(
            #'bsdf-sequence', max_sequence_len=25, initial_id=21550, substance="Fabric/cloth", show_progress=True)
