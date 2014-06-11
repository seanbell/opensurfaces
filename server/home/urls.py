from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from home.views import index, publications, dump_csv, entry_ajax
from common.utils import todo_view

urlpatterns = patterns(
    '',
    url(r'^$', index, name='home'),

    url(r'^publications/$',
        RedirectView.as_view(url='opensurfaces/', permanent=True),
        name='publications'),

    url(r'^publications/(?P<slug>\w+)/$',
        publications, name='publications'),

    url(r'^todo/$', todo_view, name='todo'),

    url(r'^entry-ajax/(?P<app_label>\w+)/(?P<model>\w+)/$',
        entry_ajax, name='entry-ajax'),

    url(r'^dump-csv/(?P<app_label>\w+)/(?P<model>\w+).csv$',
        dump_csv, name='dump-csv'),
)
