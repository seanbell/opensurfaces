from django.conf.urls import patterns, url
from accounts.views import admin_shell

urlpatterns = patterns(
    '',
    url(r'^admin-shell/$', admin_shell, name='admin-shell'),
)
