from django.conf.urls import patterns, url

from bsdfs.views import \
    bsdf_all, bsdf_all_csv, bsdf_good, bsdf_bad, bsdf_failed, bsdf_detail, \
    bsdf_wd_vote, bsdf_wd_voted_none, bsdf_wd_voted_yes, bsdf_wd_voted_no

urlpatterns = patterns(
    '',

    url(r'^(?P<v>\w+)/$', bsdf_all, name='bsdf-all'),

    url(r'^(?P<v>\w+)/good/$', bsdf_good, name='bsdf-good'),

    url(r'^(?P<v>\w+)/bad/$', bsdf_bad, name='bsdf-bad'),

    url(r'^(?P<v>\w+)/(?P<pk>\d+)/$', bsdf_detail, name='bsdf-detail'),

    url(r'^(?P<v>\w+)/all.csv$', bsdf_all_csv, name='bsdf-all-csv'),

    url(r'^(?P<v>\w+)/failed/$', bsdf_failed, name='bsdf-failed'),


    url(r'^wd/voted/none/$', bsdf_wd_voted_none,
        name='bsdf-wd-voted-none'),

    url(r'^wd/voted/yes/$', bsdf_wd_voted_yes,
        name='bsdf-wd-voted-yes'),

    url(r'^wd/voted/no/$', bsdf_wd_voted_no,
        name='bsdf-wd-voted-no'),

    url(r'^wd/vote/$', bsdf_wd_vote,
        name='bsdf-wd-vote'),

)
