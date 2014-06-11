from django.conf.urls import patterns, url
from django.views.generic import RedirectView

from mturk.views import external_incompatible, external_compatible, \
    external_task, admin_experiments, admin_preview_task, \
    admin_stats, admin_stats_table, admin_feedback, admin_pending_content, \
    admin_example, admin_example_ajax, admin_submission
from common.utils import todo_view


urlpatterns = patterns(
    '',

    ### PUBLIC

    url(r'^contribute/$', todo_view, name='mturk-contribute'),

    ### MTURK MARKETPLACE ("EXTERNAL")

    url(r'^external/incompatible/(?P<id>[-\w]+)/$',
        external_incompatible, name='mturk-external-incompatible'),

    url(r'^external/compatible/(?P<id>[-\w]+)/$',
        external_compatible, name='mturk-external-compatible'),

    url(r'^external/task/(?P<experiment_id>\d+)/$',
        external_task, name='mturk-external-task'),

    ### ADMIN

    url(r'^admin/$', RedirectView.as_view(url='/admin/experiments/', permanent=False)),

    url(r'^admin/experiments/$', admin_experiments, name='mturk-admin-experiments'),

    url(r'^admin/preview-task/(?P<experiment_id>\d+)/(?P<override>\w+)/$',
        admin_preview_task, name='mturk-admin-preview-task'),

    url(
        r'^admin/preview-task/(?P<experiment_id>\d+)/(?P<override>\w+)/(?P<hit_id>\w+)/$',
        admin_preview_task, name='mturk-admin-preview-task'),

    url(r'^admin/stats/$', admin_stats, name='mturk-admin-stats'),

    url(r'^admin/stats/(?P<experiment_slug>\w+)/table/$', admin_stats_table,
        name='mturk-admin-stats-table'),

    url(r'^admin/stats/(?P<experiment_slug>\w+)/$', admin_stats,
        name='mturk-admin-stats'),

    url(r'^admin/pending-content/$', admin_pending_content,
        name='mturk-admin-pending-content'),

    url(r'^admin/pending-content/(?P<experiment_slug>\w+)/(?P<filter_key>\w+)/$',
        admin_pending_content, name='mturk-admin-pending-content'),

    url(r'^admin/example/$', admin_example, name='mturk-admin-example'),

    url(r'^admin/example/ajax/$', admin_example_ajax,
        name='mturk-admin-example-ajax'),

    url(r'^admin/example/(?P<experiment_slug>\w+)/$',
        admin_example, name='mturk-admin-example'),

    url(r'^admin/feedback/$', admin_feedback,
        name='mturk-admin-feedback'),

    url(r'^admin/feedback/(?P<experiment_slug>\w+)/$', admin_feedback,
        name='mturk-admin-feedback'),

    url(r'^admin/submission/$', admin_submission,
        name='mturk-admin-submission'),

    url(r'^admin/submission/(?P<experiment_slug>\w+)/(?P<filter_key>\w+)/$',
        admin_submission, name='mturk-admin-submission'),
)
