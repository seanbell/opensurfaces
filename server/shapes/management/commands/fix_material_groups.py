from django.core.management.base import BaseCommand

from shapes.models import ShapeSubstance, ShapeSubstanceGroup, ShapeName


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):

        ###
        # update substances
        shape_substances = [
            'Brick', 'Cardboard', 'Carpet/rug', 'Ceramic', 'Concrete',
            'Fabric/cloth', 'Fire', 'Foliage', 'Food', 'Fur', 'Glass',
            'Granite/marble', 'Hair', 'Laminate', 'Leather', 'Metal',
            'Mirror', 'Painted', 'Paper/tissue', 'Plastic - clear',
            'Plastic - opaque', 'Rubber/latex', 'Skin', 'Sky', 'Sponge',
            'Stone', 'Tile', 'Wallpaper', 'Water', 'Wax', 'Wicker', 'Wood',
            'Linoleum', 'Styrofoam', 'Cork/corkboard',
            'Chalkboard/blackboard', 'Dirt',
        ]
        for s in shape_substances:
            if not ShapeSubstance.objects.filter(name=s).exists():
                ShapeSubstance.objects.create(name=s)
        ShapeSubstance.objects.all().update(active=False)
        ShapeSubstance.objects.filter(name__in=shape_substances).update(active=True)

        # disable existing groups
        ShapeSubstanceGroup.objects.all().update(active=False)

        ###
        # update objects


        #create_group(['Skin'], [
            #'Person'
        #])

        #create_group(['Wax'], [
            #'Candle',
        #])

        #create_group(['Mirror'], [
            #'Mirror',
        #])

        create_group(['Carpet/rug'], [
            'Floor', 'Stairs', 'Wall', 'Ceiling', 'Mat/rug - removable'
        ])

        create_group(['Wood', 'Wallpaper', 'Painted', 'Linoleum'], [
            'Bowl', 'Cabinet/cupboard', 'Ceiling', 'Chair', 'Cup', 'Mug',
            'Bottle/jug', 'Door/doorway', 'Drawer', 'Floor', 'Plate',
            'Table', 'Cutlery/utensils', 'Wall', 'Trim', 'Window',
            'Worktop/countertop', 'Shelf', 'Cutting board', 'Bookcase',
            'Ornament/sculpture', 'Stool', 'Tree/branch', 'Desk', 'Bed/bed frame',
            'Railing', 'Stairs', 'Fireplace/mantelpiece', 'Dresser/armoire', 'Column/support',
            'Television stand', 'Piano', 'Bench', 'Exhaust hood/range hood',
            'Window blinds', 'Painting/poster/picture frame', 'Toilet',
            'Firewood', 'Barrel'
        ])

        create_group(['Fabric/cloth', 'Leather'], [
            'Blanket/sheet/comforter', 'Ceiling', 'Chair',
            'Curtain', 'Pillow/cushion', 'Floor', 'Light/lamp',
            'Ornament/sculpture', 'Sofa/couch/armchair', 'Stool',
            'Wall', 'Towel', 'Tablecloth', 'Napkin/tissue/paper towel',
            'Mattress', 'Tapestry/wall quilt', 'Hat', 'Glove/mitten',
            'Shirt/blouse/sweater', 'Pants', 'Shorts', 'Skirt', 'Dress', 'Scarf',
            'Apron', 'Diaper', 'Robe/gown', 'Sock', 'Bracelet/wristband',
            'Underwear', 'Tights', 'Coat/jacket', 'Bed skirt/dust ruffle',
            'Stuffed animal/plush toy', 'Bag', 'Backpack', 'Rag/washcloth',
            'Placemat'
        ])

        create_group(['Glass'], [
            'Bowl', 'Chandelier', 'Light/lamp', 'Painting/poster', 'Sign/logo',
            'Door/doorway', 'Drawer', 'Floor', 'Food', 'Handle', 'Plate', 'Table',
            'Cutlery/utensils', 'Wall', 'Window', 'Worktop/countertop', 'Shelf',
            'Bookcase', 'Ornament/sculpture', 'Stool', 'Desk', 'Railing',
            'Stairs', 'Dresser', 'Candle', 'Glasses/sunglasses', 'Cup', 'Mug',
            'Bottle/jug', 'Wine glass', 'Jar', 'Kettle/teapot', 'Television/monitor'
        ])

        create_group(['Metal'], [
            'Bowl', 'Cabinet/cupboard', 'Ceiling', 'Chair', 'Cup', 'Mug',
            'Bottle/jug', 'Can', 'Dishwasher', 'Door/doorway', 'Drawer',
            'Faucet', 'Floor', 'Food', 'Handle', 'Kettle/teapot', 'Light/lamp',
            'Microwave', 'Oven/stove', 'Painting/poster', 'Plate',
            'Saucepan/pot/pan', 'Refrigerator', 'Sink', 'Table', 'Wall',
            'Window', 'Worktop/countertop', 'Person', 'Shelf', 'Cutting board',
            'Outlet/switch', 'Exhaust hood/range hood', 'Wire/cable'
        ])

        create_group(['Tile'], [
            'Cabinet/cupboard', 'Ceiling', 'Dishwasher', 'Door/doorway', 'Drawer',
            'Faucet', 'Floor', 'Food', 'Handle', 'Kettle/teapot', 'Light/lamp',
            'Microwave', 'Oven/stove', 'Painting/poster', 'Plate',
            'Refrigerator', 'Sink', 'Table', 'Wall', 'Window',
            'Worktop/countertop', 'Shelf', 'Cutting board', 'Outlet/switch',
            'Bathtub', 'Shower', 'Toilet',
            'Fireplace/mantelpiece', 'Exhaust hood/range hood',
        ])

        create_group(['Ceramic', 'Granite/marble', 'Laminate'], [
            'Bowl', 'Chair', 'Cup', 'Mug', 'Bottle/jug', 'Can', 'Floor',
            'Handle', 'Kettle/teapot', 'Light/lamp', 'Oven/stove',
            'Plate',  # 'Sink', 'Table', 'Towel', 'Wall',
            'Worktop/countertop', 'Clothing', 'Shelf', 'Cutting board',
            'Outlet/switch', 'Bathtub', 'Shower', 'Toilet', 'Ornament/sculpture',
            'Vase', 'Doll', 'Ceiling', 'Cabinet/cupboard', 'Drawer', 'Stairs',
            'Column/support'
        ])

        create_group(['Plastic - clear', 'Plastic - opaque'], [
            'Bowl', 'Chair', 'Cup', 'Mug', 'Bottle/jug', 'Can', 'Faucet',
            'Floor', 'Food', 'Handle', 'Kettle/teapot', 'Light/lamp',
            'Oven/stove', 'Plate', 'Sink', 'Table',
            'Towel', 'Cutlery/utensils', 'Wall', 'Worktop/countertop',
            'Shelf', 'Cutting board', 'Outlet/switch',
            'Bathtub', 'Shower', 'Toilet', 'Ornament/sculpture',
            'Door/doorway', 'Doll', 'Clock', 'Curtain', 'Painting/poster',
            'Stool', 'Vase', 'Blinds', 'Bag', 'Container', 'Basket',
            'Television/monitor', 'Electronics', 'Tongs', 'Toy', 'Ball',
            'Packaging'
        ])

        create_group(['Paper/tissue'], [
            'Book/magazine', 'Bag', 'Toilet paper', 'Napkin/tissue/paper towel',
            'Menu', 'Hat', 'Painting/poster', 'Label', 'Money', 'Map',
            'Envelope', 'Sign', 'Documents', 'Newspaper', 'Present/gift',
            'Sheet music', 'Cup', 'Calendar', 'Plate', 'Box',
            'Packaging'
        ])

        create_group(['Food'], [
            'Fruit', 'Vegetable', 'Rice', 'Pasta/noodles', 'Bread/toast',
            'Meat/fish', 'Soup', 'Water', 'Juice/smoothie', 'Sauce', 'Egg',
            'Dough', 'Pie', 'Cake', 'Pizza', 'Boiling food', 'Sandwich',
            'Coffee/tea', 'Chocolate', 'Cheese', 'Tofu', 'Cookie',
            'Spring roll', 'Muffin/cupcake', 'Butter'
        ])

        create_group(['Stone', 'Brick', 'Concrete'], [
            'Wall', 'Ceiling', 'Floor', 'Shower', 'Ornament/sculpture',
            'Stairs', 'Railing', 'Column/support', 'Shelf', 'Bathtub', 'Toilet', 'Vase',
            'Fireplace/mantelpiece', 'Exhaust hood/range hood', 'Oven/stove',
            'Window'
        ])

        create_group(['Foliage'], [
            'Tree', 'Flower', 'Leaves', 'Bush', 'Grass'
        ])

        create_group(['Rubber/latex'], [
            'Tire', 'Glove/mitten', 'Balloon', 'Chair', 'Mat/rug - removable', 'Bag', 'Shoe',
            'Handle', 'Bracelet', 'Wire/cable', 'Ball'
        ])

        create_group(['Fur'], [
            'Cat', 'Dog', 'Mouse/rat', 'Bird', 'Horse', 'Rabbit',
            'Stuffed animal/plush toy', 'Pillow/cushion',
            'Sofa/couch/armchair', 'Blanket/sheet/comforter',
            'Coat/jacket', 'Chair', 'Scarf', 'Robe/gown', 'Hat',
            'Mat/rug - removable',
        ])

        create_group(['Wicker'], [
            'Basket', 'Chair', 'Window blinds', 'Stool', 'Chair', 'Placemat',
            'Hat', 'Light/lamp', 'Shelf', 'Drawer', 'Door/doorway', 'Container',
            'Toy', 'Ornament/sculpture', 'Floor'
        ])

        create_group(['Cardboard'], [
            'Box', 'Egg carton', 'Milk carton', 'Bag', 'Tube'
        ])


def create_group(substance_names, name_names):
    print 'substances:', substance_names
    substances = [ShapeSubstance.objects.get(name=n)
                  for n in set(substance_names)]

    group = None
    for s in substances:
        if s.group:
            group = s.group
            break
    if not group:
        group = ShapeSubstanceGroup.objects.create()
    for s in substances:
        if s.group != group:
            s.group = group
            s.save()

    print 'names:', name_names
    names = [ShapeName.objects.get_or_create(name=n)[0] for n in set(name_names)]
    group.names.clear()
    for n in names:
        group.names.add(n)

    group.active = True
    group.save()
