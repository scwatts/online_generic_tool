import os
import re


from django.http import HttpResponse, Http404
from django.shortcuts import render, get_list_or_404, redirect
from django.contrib import messages
from django.conf import settings

from django.contrib.auth.decorators import login_required

from .forms import JobSubmissionForm
from .models import Job
from user_accounts.decorators import requires_verified_email
import tool.queueing


def home_page(request):
    return render(request, 'home.html', {'title': 'Home'})


@login_required
@requires_verified_email
def job_submit(request):
    # If we're recieving data then process, else present form
    if request.method == 'POST':
        form = JobSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            # Commit job info to database and write file to disk
            # TODO: validate content of input file
            job_model = form.save(request)

            # Queue the job
            redis_job = tool.queueing.enqueue(tool.queueing.submit_job, job_model)

            # Save job id and queue to SQL database
            job_model.redis_id = redis_job.get_id()
            job_model.job_queue = settings.REDIS_QUEUE_BLOCKED
            job_model.save()

            messages.success(request, 'Job submitted', extra_tags='alert-success')
    else:
        form = JobSubmissionForm()

    return render(request, 'tool/job_submit_form.html', {'form': form})


@login_required
@requires_verified_email
def job_status(request):
    user_job_list = Job.objects.filter(owner=request.user).order_by('-datetime')

    # Set input_file field to basename for rendering purposes only
    for job in user_job_list:
        job.input_file.basename = os.path.basename(job.input_file.name)

    return render(request, 'tool/job_status.html', {'user_job_list': user_job_list})


@login_required
@requires_verified_email
def serve_file(request, fileurl):
    # TODO: consider better filestorage model
    # Current we assume that all of a user's files will be under <MEDIA_ROOT>/user_<USER>
    # Authentication is (poorly, I think) done by comparing the <USER> to request.user
    # Get tokens
    token_re = re.compile(r'^.+?/user_(?P<user>.+?)/.+$')
    user = token_re.match(fileurl).group('user')

    # Ensure the user is allowed to get this file
    if str(request.user) != user:
        messages.error(request, 'File not found', extra_tags='alert-danger')
        return render('home.html')

    return xsendfile(request, fileurl)


# TODO: this may fit better somewhere else
def xsendfile(request, fileurl):
    from django.conf import settings
    from django.views.static import serve
    if settings.PROD:
        response = HttpResponse()
        response['X-Accel-Redirect'] = fileurl.encode('utf-8')
        return response
    else:
        # TODO: fix this hack
        filepath_re = re.compile(r'^.+?/(?P<filepath>.+)$')
        filepath = filepath_re.match(fileurl).group('filepath')
        document_root = settings.MEDIA_ROOT
        return serve(request, filepath, document_root)
