"""
.. describe:: ./manage.py mtconfigure

    Takes the settings out of each ``<app>/experiments.py`` file and stores
    them in the database (in :class:`mturk.models.Experiment` instances).  It
    also sets up any MTurk qualifications.
"""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = ''
    help = 'Manages the mturk pipeline'

    def handle(self, *args, **options):

        # print MTURK info
        print 'Settings Info:'
        for key in dir(settings):
            if key.startswith('MTURK') or 'DEBUG' in key:
                print '    %s: %s' % (key, getattr(settings, key))
        print ''

        if not settings.ENABLE_SSL:
            if raw_input("Warning: ENABLE_SSL=False.  Modern browsers will\n"
                         "not display non-https iframes, so workers cannot\n"
                         "do your task.  Are you sure? [y/n] ").lower() != "y":
                print 'Exiting'
                return

        if (not settings.MTURK_SANDBOX and settings.MTURK_CONFIGURE_QUALIFICATIONS):
            from mturk.tasks import configure_qualifications_task
            configure_qualifications_task()

        print 'Configuring experiments...'
        from mturk.utils import configure_all_experiments
        configure_all_experiments(show_progress=True)

        # print info
        #for exp in Experiment.objects.all().order_by('updated'):
            #print '%s:' % exp.slug
            #for field in Experiment._meta.fields:
                #print '    %s: %s' % (field, getattr(exp, field.name))
            #if exp.new_hit_settings:
                #print '  new_hit_settings:'
                #for field in ExperimentSettings._meta.fields:
                    #print '    %s: %s' % (field, getattr(exp.new_hit_settings, field.name))
            #print ''

        print ('\nNote: to actually start the hits, make sure that the '
               'celery worker is running')
