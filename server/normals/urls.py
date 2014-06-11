from django.conf.urls import patterns, url

from normals.views import \
    rectified_normal_all, rectified_normal_good, rectified_normal_bad,  \
    rectified_normal_auto, rectified_normal_best, \
    rectified_normal_curate, rectified_normal_curate_post, \
    rectified_normal_vote, rectified_normal_voted_none, \
    rectified_normal_voted_yes, rectified_normal_voted_no, \
    rectified_normal_detail


urlpatterns = patterns(
    '',

    url(r'^(?P<pk>\d+)/$', rectified_normal_detail,
        name='rectified-normal-detail'),

    url(r'^good/$', rectified_normal_good,
        name='rectified-normal-good'),

    url(r'^bad/$', rectified_normal_bad,
        name='rectified-normal-bad'),

    url(r'^auto/$', rectified_normal_auto,
        name='rectified-normal-auto'),

    url(r'^best/$', rectified_normal_best,
        name='rectified-normal-best'),

    url(r'^curate/$', rectified_normal_curate,
        name='rectified-normal-curate'),

    url(r'^curate/post/$', rectified_normal_curate_post,
        name='rectified-normal-curate-post'),

    url(r'^all/$', rectified_normal_all,
        name='rectified-normal-all'),

    url(r'^voted/none/$', rectified_normal_voted_none,
        name='rectified-normal-vote-none'),

    url(r'^voted/yes/$', rectified_normal_voted_yes,
        name='rectified-normal-voted-yes'),

    url(r'^voted/no/$', rectified_normal_voted_no,
        name='rectified-normal-voted-no'),

    url(r'^vote/$', rectified_normal_vote,
        name='rectified-normal-vote'),

)
