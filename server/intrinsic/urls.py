from django.conf.urls import patterns, url
from .views import intrinsic_comparison_detail, intrinsic_photo_all, \
    intrinsic_decomposition_by_algorithm, intrinsic_algorithm_all, \
    intrinsic_splash

urlpatterns = patterns(
    '',

    url(r'^$', intrinsic_splash, name='intrinsic-splash'),

    url(r'^comparison/(?P<pk>\d+)/$', intrinsic_comparison_detail,
        name='intrinsic-comparison-detail'),

    url(r'^judgements/$', intrinsic_photo_all,
        name='intrinsic-photo-all'),

    url(r'^judgements/(?P<category_id>\w+)/(?P<filter_key>\w+)/$', intrinsic_photo_all,
        name='intrinsic-photo-all'),

    url(r'^by-algorithm/(?P<algorithm_id>\d+)/$', intrinsic_decomposition_by_algorithm,
        name='intrinsic-decomposition-by-algorithm'),

    url(r'^by-algorithm/(?P<algorithm_id>\d+)/(?P<order_by>\S+)/$', intrinsic_decomposition_by_algorithm,
        name='intrinsic-decomposition-by-algorithm'),

    url(r'^algorithms/$', intrinsic_algorithm_all,
        name='intrinsic-algorithm-all'),
)
