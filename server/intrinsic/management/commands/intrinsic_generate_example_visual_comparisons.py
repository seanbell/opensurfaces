import os
from django.core.management.base import BaseCommand

from photos.models import Photo
from intrinsic.models import IntrinsicImagesDecomposition

from imagekit.utils import open_image
from common.utils import progress_bar


class Command(BaseCommand):
    args = ''
    help = 'Generate LaTeX Supplemental Material visual comparisons'

    def handle(self, *args, **options):
        algorithm_ids = [1141, 709, 1217, 426, 522, 633]

        photo_ids = IntrinsicImagesDecomposition.objects.filter(algorithm_id=1141) \
            .filter(mean_sum_error__isnull=False,
                    photo__stylized=False,
                    photo__rotated=False,
                    photo__synthetic=False,
                    photo__license__publishable=True,
                    photo__num_intrinsic_comparisons__gte=20,
                    #photo__aspect_ratio__lt=1,
                    ) \
            .order_by('-photo__num_intrinsic_comparisons') \
            .values_list('photo_id', flat=True)[:100]

        if not os.path.exists('visual-comparison'):
            os.makedirs('visual-comparison')

        with open('supplemental-comparisons.tex', 'w') as f:
            for photo_num, photo_id in enumerate(progress_bar(photo_ids)):
                Photo.objects.get(id=photo_id).open_image(width=512).save(
                    'visual-comparison/photo-%s.jpg' % photo_id)

                decomps = [
                    IntrinsicImagesDecomposition.objects.get(
                        algorithm_id=algorithm_id, photo_id=photo_id)
                    for algorithm_id in algorithm_ids
                ]

                for d in decomps:
                    open_image(d.reflectance_image).save('visual-comparison/decomp-%s-r.jpg' % d.id)
                    open_image(d.shading_image).save('visual-comparison/decomp-%s-s.jpg' % d.id)

                print >>f, """
                    \\begin{figure*}[tb]
                    \centering
                    \\begin{tabular}{@{}c@{\hskip 0.3em}c@{\hskip 0.3em}c@{\hskip 0.3em}c@{\hskip 0.3em}c@{\hskip 0.3em}c@{\hskip 0.3em}c@{\hskip 0.3em}c@{\hskip 0.3em}}
                        \\gfxw{0.135}{visual-comparison/photo-%s.jpg} &
                        \\rotatebox{90}{\small{Reflectance $\mathbf{R}$}} &
                    """.strip() % photo_id

                for i, d in enumerate(decomps):
                    print >>f, r"\gfxw{0.135}{visual-comparison/decomp-%s-r.jpg}".strip() % d.id
                    if i < len(decomps) - 1:
                        print >>f, "&"

                print >>f, r"\\ & \rotatebox{90}{\small{Shading $S$}} &"

                for i, d in enumerate(decomps):
                    print >>f, r"\gfxw{0.135}{visual-comparison/decomp-%s-s.jpg}".strip() % d.id
                    if i < len(decomps) - 1:
                        print >>f, "&"

                print >>f, r"\\ & &"

                for i, d in enumerate(decomps):
                    if i == 0:
                        print >>f, r'\MetricName{} = %.1f\%%' % (d.mean_error * 100.0)
                    else:
                        print >>f, r'%.1f\%%' % (d.mean_error * 100.0)
                    if i < len(decomps) - 1:
                        print >>f, "&"

                print >>f, """
                    \\\\
                    Image $\\mathbf{I}$ &
                    &
                    Our algorithm &
                    \\cite{zhao-PAMI2012} &
                    \\cite{garces2012} &
                    \\cite{shen-CVPR2011b} &
                    Retinex (gray) &
                    Retinex (color)
                    \\end{tabular}
                    \\vspace{-6pt}
                    \\caption{\\new{%%
                    Visual comparison of our algorithm against several recent open-source
                    algorithms.  Each algorithm uses the best parameters found from training
                    (i.e., minimizes mean \\MetricNameDelta{} across all photos).
                    OpenSurfaces Photo ID: %s.
                    }}
                    \\label{fig:visual-comparison-%s}
                    \\vspace{-6pt}
                    \\end{figure*}
                    """.strip() % (photo_id, photo_id)

                if (photo_num + 1) % 3 == 0:
                    print >>f, r"\clearpage"
