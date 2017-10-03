"""URL patterns."""

from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^login/$', auth_views.login, name='login', kwargs={'template_name': 'flasharray/login.html'}),
    url(r'^logout/$', auth_views.logout, name='logout', kwargs={'next_page': '/'}),
    url(r'home.html', views.index, name='home'),
    url(r'logs.html', views.logs, name='logs'),
    url(r'^create_array', views.FlashArrayCreate.as_view(), name='create_array'),
    url(r'^delete_array/(?P<pk>[\w-]+)$', views.FlashArrayDelete.as_view(), name='delete_array'),
    url(r'^update_array/(?P<pk>[\w-]+)$', views.FlashArrayUpdate.as_view(), name='update_array'),
]
