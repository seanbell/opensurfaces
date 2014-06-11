import os
from celery import shared_task

from imagekit.utils import save_image
from bsdfs.models import ShapeBsdfLabel_wd


@shared_task
def save_substance_reflectance_grid(
        outdir, initial_id=None,
        max_sequence_len=None, ncols=25,
        show_progress=False, substance=None):

    try:
        os.makedirs(outdir)
    except OSError as e:
        print e

    print 'Fetching all BSDFs...'

    # fetch all bsdfs
    qset = ShapeBsdfLabel_wd.objects.filter(
        color_correct=True, gloss_correct=True, shape__photo__inappropriate=False,
        #color_correct_score__gte=0.1,
        #gloss_correct_score__gte=0.1,
        shape__photo__license__publishable=True)

    if substance:
        qset = qset.filter(shape__substance__name=substance)

    bsdfs = list(qset.extra(
        select={'correct_score': 'color_correct_score + gloss_correct_score'},
        order_by=('-correct_score',)
    ))

    max_sequence_len = min(max_sequence_len, len(bsdfs))
    print 'Constructing sequence (%s items)...' % max_sequence_len

    # start with a more interesting shape
    bsdf = bsdfs[0]
    for b in bsdfs:
        if b.id == initial_id:
            bsdf = b
            break
    bsdf_sequence = [bsdf]

    shape_ids = set()
    shape_ids.add(bsdf.shape_id)

    try:
        while True:

            best_color_d = 1e10
            best_gloss_b = None

            best_gloss_d = 1e10
            best_color_b = None

            for b in bsdfs:
                if b.shape_id in shape_ids:
                    continue

                color_d = bsdf.color_distance(b)
                if color_d <= best_color_d:
                    best_color_d = color_d
                    best_color_b = b

                if color_d <= 2.3:
                    gloss_d = bsdf.gloss_distance(b)
                    if gloss_d < best_gloss_d:
                        best_gloss_d = gloss_d
                        best_gloss_b = b

            best_b = best_gloss_b if best_gloss_b else best_color_b
            if best_b:
                print best_b.id
                bsdf = best_b
                bsdf_sequence.append(best_b)
                shape_ids.add(best_b.shape_id)
                if max_sequence_len and len(bsdf_sequence) >= max_sequence_len:
                    break
            else:
                break

            if show_progress:
                print len(bsdf_sequence)
    except KeyboardInterrupt:
        print 'Search interrupted: using %s items' % len(bsdf_sequence)

    print 'Fetching shapes...'
    image_pairs = [
        (b.image_blob, b.shape.image_square_300)
        for b in bsdf_sequence
    ]

    print 'Constructing image...'

    # save result
    from common.utils import create_image_pair_grid_list
    out = create_image_pair_grid_list(
        image_pairs, ncols=ncols, size=256, show_progress=True)

    print 'Saving result...'
    if substance:
        outname = os.path.join(
            outdir, '%s.png' % substance.replace('/', '-').lower())
    else:
        outname = os.path.join(outdir, 'blob-sequence.png')
    with open(outname, 'wb') as outfile:
        save_image(out, outfile, format="PNG")
