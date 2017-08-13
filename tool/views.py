from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages

from django.contrib.auth.decorators import login_required

import django_rq

from .forms import JobSubmissionForm
from user_accounts.decorators import requires_verified_email
import tool.queueing


def home_page(request):
    return render(request, 'home.html', {'title': 'Home'})


def job_create(request):
    return HttpResponse('The job creatation page')


@login_required
@requires_verified_email
def job_submit(request):
    # If we're recieving data then process, else present form
    if request.method == 'POST':
        form = JobSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            # Commit job info to database and write file to disk
            # TODO: validate content of input file
            job = form.save(request)

            # Queue the job
            #queue = django_rq.get_queue('default')
            #queue.enqueue(tool.queueing.submit_job, job)
            queue = django_rq.enqueue(tool.queueing.submit_job, job)
            messages.success(request, 'Job submitted', extra_tags='alert-success')
    else:
        form = JobSubmissionForm()

    return render(request, 'job_submit_form.html', {'form': form})


def job_status(request):
    return HttpResponse('The job status page')
