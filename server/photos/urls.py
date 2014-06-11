from django.conf.urls import patterns, url
from photos.views import photo_by_category, photo_detail, photo_curate

urlpatterns = patterns(
    '',

    url(r'^$',
        photo_by_category, name='photo-by-category'),

    url(r'^scene/(?P<category_id>\w+)/$',
        photo_by_category, name='photo-by-category'),

    url(r'^scene/(?P<category_id>\w+)/(?P<filter_key>\w+)/$',
        photo_by_category, name='photo-by-category'),

    url(r'^(?P<pk>\d+)/$',
        photo_detail, name='photo-detail'),

    url(r'^curate/$', photo_curate, name='photo-curate'),
)
