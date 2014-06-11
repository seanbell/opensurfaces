from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from clint.textui import progress

from shapes.models import MaterialShape, ShapeSubstance, ShapeSubstanceLabel


class Command(BaseCommand):
    args = ''
    help = 'Update substances'

    def handle(self, *args, **options):
        if raw_input("This will destroy many labels and merge groups; are you sure? [y/N] ").lower() != "y":
            print 'Exiting'
            return

        update_descriptions()
        #fix_labels()


def update_descriptions():
    print 'Updating descriptions...'

    u('Brick', 45500,
      'Small rectangular blocks typically made of fired or sun-dried clay')
    u('Cardboard', 74584, 'Pasteboard or stiff paper')
    u('Carpet', 61134, 'Floor or stair covering made from thick woven fabric')
    u('Ceramic', 89534, 'Hard brittle material produced from nonmetallic minerals by firing at high temperature')
    u('Concrete', 49829, 'Strong hard building material composed of sand and gravel and cement and water')
    u('Fabric/cloth', 110486, 'Artifact made by weaving or felting or knitting or crocheting natural or synthetic fibers')
    u('Fire', 113412, 'Combustion of materials producing heat and light')
    u('Foliage', 115278, 'Plant leaves, flowers, and branches')
    u('Food', 111661,
      'Nutritious substance that people or animals eat or drink')
    u('Fur', 44611, 'Short, fine, soft hair of certain animals')
    u('Glass', 115212,
      'Hard, brittle substance, typically transparent or translucent')
    u('Granite', 36771,
      "Plutonic igneous rock having visibly crystalline texture.  Note that laminate that looks like granite should be labeled as 'Granite'")
    u('Hair', 100954, 'Threadlike strands growing from the skin of people')
    u('Laminate', 78695, 'Composite made of plastic resin and cellulose paper with a decorative finish.  If it is designed to look like another surface, please select that name instead')
    u('Leather', 93463, 'Animal skin made smooth and flexible by removing the hair and then tanning')
    u('Marble', 46360, 'Hard crystalline metamorphic rock that takes a high polish, typically with streaks of color')
    u('Metal', 115760, 'Solid material that is typically hard, shiny, malleable, fusible, and ductile')
    u('Mirror', 49007, 'Polished surface that reflects a clear image')
    u('Painted', 99795, 'Surface covered with a layer of opaque paint (e.g. acrylic or latex paint)')
    u('Paper', 75737,
      'Thin sheets from the pulp of wood or other fibrous substances')
    u('Plastic - clear', 79991, 'Transparent synthetic material made from a wide range of organic polymers (does transmit light)')
    u('Plastic - opaque', 101288, 'Opaque synthetic material made from a wide range of organic polymers (does not transmit light)')
    u('Rubber/latex', 102458, 'Elastic material obtained from the latex sap of trees')
    u('Skin', 92544, 'Thin layer of tissue forming the natural outer covering of the body of a person or animal')
    u('Sky', 118157, 'The atmosphere and outer space as viewed from the earth')
    u('Sponge', 94587, 'Porous mass of interlacing fibers used to absorb water')
    u('Stone', 105043,
      'Hard, solid, nonmetallic mineral matter of which rock is made')
    u('Tile', 72815, "Flat thin rectangular slab used to cover surfaces.  Note that laminate that looks like tile should be labeled as 'Tile'")
    u('Wallpaper', 111933, 'Decorative paper for the walls of rooms')
    u('Water', 37861, 'Liquid found in lakes and rivers')
    u('Wax', 101287,
      'Insoluble compounds that are malleable near ambient temperatures')
    u('Wicker', 107330, 'Interlaced slender branches')
    u('Wood', 100704, "Hard fibrous substance under the bark of trees.  Note that laminate that looks like wood should be labeled as 'Wood'")


def u(name_string, representative_shape_id, description):
    substance, __ = ShapeSubstance.objects.get_or_create(
        name=name_string,
        defaults={'user': User.objects.get_or_create(
            username='admin')[0].get_profile()},
    )
    substance.description = description
    substance.representative_shape_id = representative_shape_id
    substance.save()


def fix_labels():
    print 'Collapsing labels...'

    # fetch some labels
    paper = ShapeSubstance.objects.get(name='Paper')
    not_on_list = ShapeSubstance.objects.get(name='Not on list')
    more_than_one = ShapeSubstance.objects.get(name='More than one material')
    marble = ShapeSubstance.objects.get(name='Marble')
    granite = ShapeSubstance.objects.get(name='Granite')
    water = ShapeSubstance.objects.get(name='Water')
    stone = ShapeSubstance.objects.get(name='Stone')
    carpet = ShapeSubstance.objects.get(name='Carpet')
    concrete = ShapeSubstance.objects.get(name='Concrete')
    plaster = ShapeSubstance.objects.get(name='Plaster')
    fur = ShapeSubstance.objects.get(name='Fur')

    # collapse paper
    ShapeSubstanceLabel.objects \
        .filter(substance__name__startswith='Paper ') \
        .update(substance=paper)

    # collapse painted
    painted = ShapeSubstance.objects.get(name='Painted')
    ShapeSubstanceLabel.objects \
        .filter(substance__name__in=[
            'Wood - painted', 'Wallboard - painted']) \
        .update(substance=painted)

    # collapse wood
    wood = ShapeSubstance.objects.get(name='Wood')
    ShapeSubstanceLabel.objects \
        .filter(substance__name__startswith='Wood ') \
        .update(substance=wood)

    # reset laminate
    laminate = ShapeSubstance.objects.get(name='Laminate')
    ShapeSubstanceLabel.objects.filter(substance=laminate) \
        .update(invalid=True)

    # reset "I can't tell"
    i_cant_tell = ShapeSubstance.objects.get(name="I can't tell")
    ShapeSubstanceLabel.objects.filter(
        substance=i_cant_tell).update(invalid=True)

    # recompute substance labels
    print 'Recomputing substance labels...'
    MaterialShape.objects.all().update(substance=None)
    shape_ids = ShapeSubstanceLabel.objects.distinct('shape') \
        .values_list('shape_id', flat=True).order_by()

    for shape_id in progress.bar(shape_ids):
        with transaction.atomic():
            shape = MaterialShape.objects.get(id=shape_id)

            # reset labels split between various groups
            substance_ids = shape.substances.values_list('substance_id', flat=True)
            if ((painted.id in substance_ids and wood.id in substance_ids) or
                (painted.id in substance_ids and paper.id in substance_ids) or
                (painted.id in substance_ids and stone.id in substance_ids) or
                (marble.id in substance_ids and granite.id in substance_ids) or
                (marble.id in substance_ids and stone.id in substance_ids) or
                (granite.id in substance_ids and stone.id in substance_ids) or
                (marble.id in substance_ids and carpet.id in substance_ids) or
                (laminate.id in substance_ids) or
                (concrete.id in substance_ids) or
                (plaster.id in substance_ids) or
                (water.id in substance_ids) or
                (fur.id in substance_ids) or
                (not_on_list.id in substance_ids)):
                for substance in shape.substances.all():
                    substance.mark_invalid()
            elif (more_than_one.id in substance_ids):
                for substance in shape.substances.exclude(substance=more_than_one):
                    substance.mark_invalid()

            # recompute most common substance
            shape.update_entropy()
