from django.core.management.base import BaseCommand

from common.models import PaperCitation
from intrinsic.models import IntrinsicImagesAlgorithm


class Command(BaseCommand):
    args = ''
    help = 'Fix intrinsic images citations'

    def handle(self, *args, **options):

        bell2014_densecrf, _ = PaperCitation.objects.get_or_create(
            slug='bell2014_densecrf',
            authors='Sean Bell, Kavita Bala, Noah Snavely',
            title='Intrinsic Images in the Wild',
            journal='ACM Transactions on Graphics (SIGGRAPH 2014)',
            inline_citation='[Bell et al. 2014]',
            url='http://intrinsic.cs.cornell.edu',
        )

        zhao2012_nonlocal, _ = PaperCitation.objects.get_or_create(
            slug='zhao2012_nonlocal',
            authors='Qi Zhao, Ping Tan, Qiang Dai, Li Shen, Enhua Wu, Stephen Lin',
            title='A Closed-form Solution to Retinex with Non-local Texture Constraints',
            journal='IEEE Transaction on Pattern Analysis and Machine Intelligence (TPAMI)',
            inline_citation='[Zhao et al. 2012]',
            url='http://www.ece.nus.edu.sg/stfpage/eletp/Papers/pami12_intrinsic.pdf',
        )

        garces2012_clustering, _ = PaperCitation.objects.get_or_create(
            slug='garces2012_clustering',
            authors='Elena Garces, Adolfo Munoz, Jorge Lopez-Moreno, Diego Gutierrez',
            title='Intrinsic Images by Clustering',
            journal='Computer Graphics Forum (Eurographics Symposium on Rendering)',
            inline_citation='[Garces et al. 2012]',
            url='http://www-sop.inria.fr/reves/Basilic/2012/GMLG12/',
        )

        grosse2009_retinex, _ = PaperCitation.objects.get_or_create(
            slug='grosse2009_retinex',
            authors='Roger Grosse, Micah K. Johnson, Edward H. Adelson, William T. Freeman',
            title='Ground truth dataset and baseline evaluations for intrinsic image algorithms',
            journal='Proceedings of the International Conference on Computer Vision (ICCV)',
            inline_citation='[Grosse et al. 2009]',
            url='http://www.cs.toronto.edu/~rgrosse/intrinsic/',
        )

        shen2011_optimization, _ = PaperCitation.objects.get_or_create(
            slug='shen2011_optimization',
            authors='Jianbing Shen, Xiaoshan Yang, Yunde Jia, Xuelong Li',
            title='Intrinsic Images Using Optimization',
            journal='Proceedings of Computer Vision and Pattern Recognition (CVPR)',
            inline_citation='[Shen et al. 2011]',
            url='http://cs.bit.edu.cn/~shenjianbing/cvpr11.htm',
        )

        print IntrinsicImagesAlgorithm.objects \
            .filter(slug='bell2014_densecrf') \
            .update(citation=bell2014_densecrf)

        print IntrinsicImagesAlgorithm.objects \
            .filter(slug='zhao2012_nonlocal') \
            .update(citation=zhao2012_nonlocal)

        print IntrinsicImagesAlgorithm.objects \
            .filter(slug='garces2012_clustering') \
            .update(citation=garces2012_clustering)

        print IntrinsicImagesAlgorithm.objects \
            .filter(slug='grosse2009_color_retinex') \
            .update(citation=grosse2009_retinex)

        print IntrinsicImagesAlgorithm.objects \
            .filter(slug='grosse2009_grayscale_retinex') \
            .update(citation=grosse2009_retinex)

        print IntrinsicImagesAlgorithm.objects \
            .filter(slug='shen2011_optimization') \
            .update(citation=shen2011_optimization)
