# admin
from django.contrib import admin
admin.autodiscover()

# urls
from django.conf.urls import patterns, include, url
from accounts.views import SignupView, SignupViewAjax, LoginView, LoginViewAjax
urlpatterns = patterns(
    '',
    url(r'^', include('home.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^photos/', include('photos.urls')),
    url(r'^bsdfs/', include('bsdfs.urls')),
    url(r'^normals/', include('normals.urls')),
    url(r'^shapes/', include('shapes.urls')),
    url(r'^mturk/', include('mturk.urls')),
    url(r'^analytics/', include('analytics.urls')),
    url(r'^intrinsic/', include('intrinsic.urls')),
    url(r'^accounts/', include('accounts.urls')),

    # django-user-accounts with some custom modifications
    url(r'^account/signup/$', SignupView.as_view(), name='account_signup'),
    url(r'^account/login/$', LoginView.as_view(), name='account_login'),
    url(r'^account/signup-ajax/$', SignupViewAjax.as_view(), name='account_signup_ajax'),
    url(r'^account/login-ajax/$', LoginViewAjax.as_view(), name='account_login_ajax'),
    url(r'^account/', include('account.urls')),

    # captcha
    url(r'^captcha/', include('captcha.urls')),
)

# media files
from django.conf.urls.static import static
from django.conf import settings
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# static files
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()

# necessary workaround for correclty displaying error 500 pages
# see:
# https://github.com/jezdez/django_compressor/pull/206
# and:
# http://stackoverflow.com/questions/13633508/django-handler500-as-a-class-based-view
from common.views import Handler500
handler500 = Handler500.as_error_view()
