from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView


# TODO: change of all these dones/ confirmation pages to django messages
urlpatterns = [
    url(r'^register_account/', views.RegisterAccount.as_view(), name='register_account'),

    url(r'^register_account_done/', TemplateView.as_view(template_name='register/done.html'),
        name='register_account_done'),

    url(r'^email_verify/(?P<token>[a-z0-9]+)*$', views.EmailVerify.as_view(), name='email_verify'),

    url(r'^resend_verification/$', views.ResendVerification.as_view(), name='resend_verification'),


    url(r'^login/$', auth_views.login,
        {'template_name': 'login.html',
         'redirect_authenticated_user': True},
        name='login'),
    url(r'^logout/$', views.Logout.as_view(), name='logout'),


    url(r'^account/$', views.Account.as_view(), name='account'),

    url(r'^email_change/$', views.EmailChange.as_view(), name='email_change'),


    url('^password_change/$', views.PasswordChange.as_view(), name='password_change'),

    url(r'^password_reset/$', views.PasswordReset.as_view(), name='password_reset'),

    url(r'^password_reset_confirm/(?P<token>.+?)/(?P<uidb64>.+?)/$',
        views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
]
