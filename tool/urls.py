from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.HomePage.as_view(), name='home_page'),
    url(r'^job_submit/', views.JobSubmit.as_view(), name='job_submit'),
    url(r'^job_status/', views.JobStatus.as_view(), name='job_status'),
    url(r'^job_view/(?P<job_id>[0-9]*)/', views.JobView.as_view(), name='job_view'),
    url(r'^serve_file/(?P<run>[0-9]+)/(?P<directory>[^/]+)/(?P<filename>[^/]+)/',
        views.ServeFile.as_view(), name='serve_file'),
]
