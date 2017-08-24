from django.urls import reverse
from django import template

register = template.Library()

@register.filter
def current_url(request, pattern):
    return request.path == reverse(pattern)
