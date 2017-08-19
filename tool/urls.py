from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.home_page, name='home_page'),
    url(r'^job_submit/', views.job_submit, name='job_submit'),
    url(r'^job_status/', views.job_status, name='job_status'),
    url(r'^serve_file/(?P<fileurl>.+)/', views.serve_file,
        name='serve_file'),
]
