from django.http import HttpResponse
from django.shortcuts import render


def home_page(request):
    return render(request, 'home.html', {'title': 'Home'})


def job_create(request):
    return HttpResponse('The job creatation page')


def job_submit(request):
    return HttpResponse('The job submit page')


def job_status(request):
    return HttpResponse('The job status page')
