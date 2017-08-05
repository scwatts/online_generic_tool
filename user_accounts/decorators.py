from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages


def requires_verified_email(func):
    def decorator(request, *args, **kwargs):
        if request.user.is_verified:
            return func(request, *args, **kwargs)
        else:
            messages.error(request, 'You must verify your email first', extra_tags='alert-warning')
            return redirect(reverse('home_page'))

    return decorator
