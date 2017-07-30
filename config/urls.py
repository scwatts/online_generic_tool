from django.conf.urls import url, include


urlpatterns = [
    url('', include('tool.urls')),
    url('', include('user_accounts.urls')),
]
