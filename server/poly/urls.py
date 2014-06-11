from django.conf.urls import patterns, url
from polys.views import poly_spec

urlpatterns = patterns(
    '',
    url(r'^test/$', poly_spec, name='poly-spec'),
)
