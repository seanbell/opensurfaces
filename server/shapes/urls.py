from django.conf.urls import patterns, url

from shapes.views import \
    material_shape_all, material_shape_detail, material_shape_search, \
    material_shape_by_user, material_shape_by_quality, \
    material_shape_by_planarity, \
    material_shape_curate_planarity, material_shape_curate_planarity_post, \
    material_shape_by_substance, material_shape_by_name, material_shape_rectified, \
    material_shape_by_rejected, material_shape_by_synthetic, \
    material_shape_by_time, material_shape_by_vertices, \
    material_shape_all_csv, material_shape_bsdfs_csv, \
    name_all, substance_all


urlpatterns = patterns(
    '',

    url(r'^material-shapes/$', material_shape_all,
        name='material-shape-all'),

    url(r'^material-shapes/search/$', material_shape_search,
        name='material-shape-search'),

    url(r'^material-shapes/all.csv$', material_shape_all_csv,
        name='material-shape-all-csv'),

    url(r'^material-shapes/(?P<pk>\d+)/$', material_shape_detail,
        name='material-shape-detail'),

    url(r'^material-shapes/(?P<pk>\d+)/(?P<v>v\d+)/bsdfs.csv$',
        material_shape_bsdfs_csv, name='material-shape-bsdfs-csv'),

    url(r'^material-shapes/by-user/$', material_shape_by_user,
        name='material-shape-by-user'),

    url(r'^material-shapes/by-time/$', material_shape_by_time,
        name='material-shape-by-time'),

    url(r'^material-shapes/by-vertices/$', material_shape_by_vertices,
        name='material-shape-by-vertices'),

    url(r'^material-shapes/by-quality/$', material_shape_by_quality,
        name='material-shape-by-quality'),

    url(r'^material-shapes/by-planarity/$', material_shape_by_planarity,
        name='material-shape-by-planarity'),

    url(r'^material-shapes/curate-planarity/$',
        material_shape_curate_planarity,
        name='material-shape-curate-planarity'),

    url(r'^material-shapes/curate-planarity/post/$',
        material_shape_curate_planarity_post,
        name='material-shape-curate-planarity-post'),

    url(r'^material-shapes/by-substance/$', material_shape_by_substance,
        name='material-shape-by-substance'),

    url(r'^material-shapes/by-name/$', material_shape_by_name,
        name='material-shape-by-name'),

    url(r'^material-shapes/by-rejected/$', material_shape_by_rejected,
        name='material-shape-by-rejected'),

    url(r'^material-shapes/by-synthetic/$', material_shape_by_synthetic,
        name='material-shape-by-synthetic'),


    url(r'^name/all/$', name_all, name='name-all'),

    url(r'^name/all/(?P<pk>\d+)/$', name_all, name='name-all'),

    url(r'^substance/all/$', substance_all, name='substance-all'),

    url(r'^substance/all/(?P<pk>\d+)/$', substance_all, name='substance-all'),


    url(r'^material-shapes/rectified/$', material_shape_rectified,
        name='material-shape-rectified'),

)
