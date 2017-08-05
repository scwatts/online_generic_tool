from django.urls import reverse_lazy
from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView


# TODO: change of all these dones/ confirmation pages to django messages
urlpatterns = [
    url(r'^register_account/', views.register_account, name='register_account'),

    url(r'^register_account_done/', TemplateView.as_view(template_name='register/done.html'),
        name='register_account_done'),

    url(r'^email_verify/(?P<token>[a-z0-9]+)*$', views.email_verify, name='email_verify'),

    url(r'^resend_verification/$', views.resend_verification, name='resent_verification'),


    url(r'^login/$', auth_views.login,
        {'template_name': 'login.html',
         'redirect_authenticated_user': True},
        name='login'),
    url(r'^logout/$', views.logout, name='logout'),


    url(r'^account/$', views.account, name='account'),

    url(r'^email_change/$', views.email_change, name='email_change'),


    url('^password_change/$', views.password_change, name='password_change'),

    url(r'^password_reset/$', views.password_reset, name='password_reset'),

    url(r'^password_reset_confirm/(?P<token>.+?)/(?P<uidb64>.+?)/$', views.password_reset_confirm,
        name='password_reset_confirm'),
]
