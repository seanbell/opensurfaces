import numpy as np

from django.core.management.base import BaseCommand
from django.db.models import Q

from intrinsic.models import IntrinsicPointComparison
from common.utils import progress_bar

import matplotlib
matplotlib.use('Agg')


class Command(BaseCommand):
    args = ''
    help = 'Perform analysis of synthetic images'

    def handle(self, *args, **options):
        print "Fetching comparisons..."
        comparisons = IntrinsicPointComparison.objects \
            .filter(darker__isnull=False,
                    point1__opaque=True,
                    point2__opaque=True,
                    point1__synthetic_diff_fraction__gte=0.9,
                    point2__synthetic_diff_fraction__gte=0.9) \
            .select_related('point1', 'point2')

        self.threshold_plots(comparisons)
        self.whd_plots(comparisons)

    def threshold_plots(self, comparisons):
        lines = []
        lines.append((
            'all',
            self.prepare_plot_thresholds(comparisons)
        ))

        lines.append((
            'both textured',
            self.prepare_plot_thresholds(
                comparisons.filter(
                    point1__synthetic_diff_cv__gt=0.01,
                    point2__synthetic_diff_cv__gt=0.01,
                )
            )
        ))

        lines.append((
            'both untextured',
            self.prepare_plot_thresholds(
                comparisons.filter(
                    point1__synthetic_diff_cv__lt=0.01,
                    point2__synthetic_diff_cv__lt=0.01,
                )
            )
        ))

        lines.append((
            'not both textured',
            self.prepare_plot_thresholds(
                comparisons.filter(
                    Q(point1__synthetic_diff_cv__lt=0.01) |
                    Q(point2__synthetic_diff_cv__lt=0.01)
                )
            )
        ))

        lines.append((
            'exactly one textured',
            self.prepare_plot_thresholds(
                comparisons.filter(
                    Q(point1__synthetic_diff_cv__lt=0.01) |
                    Q(point2__synthetic_diff_cv__lt=0.01)
                ).exclude(
                    point1__synthetic_diff_cv__lt=0.01,
                    point2__synthetic_diff_cv__lt=0.01,
                )
            )
        ))
        self.plot('thresholds.png', lines, xlabel='true diffuse color ratio',
                  ylabel='fraction correct', axis=[1, 1.5, 0, 1], legend_loc='lower right')

    def prepare_plot_thresholds(self, comparisons):
        print "Preparing %s comparisons" % len(comparisons)
        ratios = np.linspace(1.001, 1.5, 512)
        fractions = []
        for r in progress_bar(ratios):
            num = 0
            den = 0
            for c in comparisons:
                if (c.point1.synthetic_diff_intensity /
                        c.point2.synthetic_diff_intensity > r):

                    if c.darker == '2':
                        num += 1
                    den += 1

                elif (c.point2.synthetic_diff_intensity /
                        c.point1.synthetic_diff_intensity > r):

                    if c.darker == '1':
                        num += 1
                    den += 1

            if den:
                fractions.append(float(num) / float(den))
            else:
                fractions.append(0)

        return ratios, fractions, len(comparisons)

    def whd_plots(self, comparisons):

        lines = []
        lines.append((
            'all',
            self.prepare_plot_whd(comparisons)
        ))

        lines.append((
            'both textured',
            self.prepare_plot_whd(
                comparisons.filter(
                    point1__synthetic_diff_cv__gt=0.01,
                    point2__synthetic_diff_cv__gt=0.01,
                )
            )
        ))

        lines.append((
            'both untextured',
            self.prepare_plot_whd(
                comparisons.filter(
                    point1__synthetic_diff_cv__lt=0.01,
                    point2__synthetic_diff_cv__lt=0.01,
                )
            )
        ))

        either_untextured = (
            'not both textured',
            self.prepare_plot_whd(
                comparisons.filter(
                    Q(point1__synthetic_diff_cv__lt=0.01) |
                    Q(point2__synthetic_diff_cv__lt=0.01)
                )
            )
        )
        lines.append(either_untextured)

        lines.append((
            'exactly one textured',
            self.prepare_plot_whd(
                comparisons.filter(
                    Q(point1__synthetic_diff_cv__lt=0.01) |
                    Q(point2__synthetic_diff_cv__lt=0.01)
                ).exclude(
                    point1__synthetic_diff_cv__lt=0.01,
                    point2__synthetic_diff_cv__lt=0.01,
                )
            )
        ))

        self.plot('whd.png', lines, xlabel='delta', ylabel='WHD', axis=[0, 0.8, 0, 0.35])

        ##

        lines = [either_untextured]
        lines.append((
            'either untextured, no E',
            self.prepare_plot_whd(
                comparisons.filter(
                    Q(point1__synthetic_diff_cv__lt=0.01) |
                    Q(point2__synthetic_diff_cv__lt=0.01)
                ).filter(Q(darker='1') | Q(darker='2'))
            )
        ))
        lines.append((
            'either untextured, only E',
            self.prepare_plot_whd(
                comparisons.filter(
                    Q(point1__synthetic_diff_cv__lt=0.01) |
                    Q(point2__synthetic_diff_cv__lt=0.01)
                ).filter(darker='E')
            )
        ))

        self.plot('whd-by-ans.png', lines, xlabel='delta', ylabel='WHD', axis=[0, 0.8, 0, 0.35])

    def prepare_plot_whd(self, comparisons):
        print "Preparing %s comparisons" % len(comparisons)
        deltas = np.linspace(0.001, 0.8, 512)
        whds = [self.whd(comparisons, thresh=t) for t in deltas]
        return deltas, whds, len(comparisons)

    def whd(self, comparisons, thresh=0.05):
        neq_thresh = 1.0 / (1.0 + thresh)
        eq_thresh = 1.0 + thresh

        error_sum = 0
        error_total = 0
        for c in comparisons:
            l1 = c.point1.synthetic_diff_intensity
            l2 = c.point2.synthetic_diff_intensity

            if c.darker == "1":  # l1 < l2
                error_sum += 0 if l1 / max(l2, 1e-10) < neq_thresh else c.darker_score
            elif c.darker == "2":  # l2 < l1
                error_sum += 0 if l2 / max(l1, 1e-10) < neq_thresh else c.darker_score
            elif c.darker == "E":  # l1 - l2
                ratio = max(l1, l2) / max(min(l1, l2), 1e-10)
                error_sum += 0 if ratio < eq_thresh else c.darker_score
            else:
                raise ValueError("Unknown value of darker: %s" % c.darker)

            error_total += c.darker_score

        if error_total:
            return error_sum / error_total
        else:
            return 0.0

    def plot(self, filename, lines, xlabel=None, ylabel=None, title=None, axis=None, legend_loc='upper right'):
        print "Saving %s..." % filename

        import matplotlib.pyplot as plt
        labels = []
        for (label, (x, y, n)) in lines:
            plt.plot(x, y)
            if n:
                labels.append('%s (%s)' % (label, n))
            else:
                labels.append(label)
        plt.legend(labels, loc=legend_loc)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)
        if title:
            plt.title(title)
        if axis:
            plt.axis(axis)
        plt.savefig(filename)
        plt.close()
