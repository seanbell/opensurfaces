from django.conf.urls import patterns, url
from .views import analytics_material_shapes, \
    analytics_bsdf_wd, analytics_rectified_normal

urlpatterns = patterns(
    '',

    url(r'^material-shapes/$', analytics_material_shapes,
        name='analytics-material-shapes'),

    url(r'^bsdf-wd/$', analytics_bsdf_wd,
        name='analytics-bsdf-wd'),

    url(r'^rectified-normal/$', analytics_rectified_normal,
        name='analytics-rectified-normal'),

)
