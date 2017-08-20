import os
import pathlib
import re


from django.http import HttpResponse, Http404
from django.shortcuts import render, get_list_or_404, redirect, reverse
from django.contrib import messages
from django.conf import settings

from django.contrib.auth.decorators import login_required

from .forms import JobSubmissionForm
from .models import Job
from user_accounts.decorators import requires_verified_email
import tool.queueing


FILES_EXTENSIONS = ['err', 'faa', 'ffn', 'fna', 'fsa', 'gbk',
                    'gff', 'log', 'sqn', 'tbl', 'tsv', 'txt']


def home_page(request):
    # Get the number of jobs queued, running, and finished
    context = {
            'title': 'Home',
            'jobs_queued': len(Job.objects.filter(status='submitted')),
            'jobs_running': len(Job.objects.filter(status='running')),
            'jobs_completed': len(Job.objects.filter(status='completed'))
            }

    return render(request, 'home.html', context=context)


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
            redis_job = tool.queueing.enqueue(tool.queueing.execute_job, job_model.id)

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
    user_job_list = Job.objects.filter(owner=request.user).order_by('-start_time')

    # Set input_file field to basename for rendering purposes only
    for job in user_job_list:
        job.input_file.basename = os.path.basename(job.input_file.name)

    return render(request, 'tool/job_status.html', {'user_job_list': user_job_list})


@login_required
@requires_verified_email
def job_view(request, job_id=None):
    # Get job model instance
    job = Job.objects.get(id=job_id)

    # Check that job has ended
    if job.status != 'completed':
        messages.warning(request, 'Cannot view job', extra_tags='alert-warning')
        return redirect(reverse('job_status'))

    # Make sure that the user owns this job entry
    if job.owner != request.user:
        messages.error(request, 'This is not your job', extra_tags='alert-danger')
        return redirect(reverse('job_status'))

    context = {'files': ('run.%s' % ext for ext in FILES_EXTENSIONS),
               'job_id': job_id,
               'input_file': os.path.basename(job.input_file.name),
               'start_time': job.start_time,
               'duration': job.duration}

    return render(request, 'tool/job_view.html', context=context)


@login_required
@requires_verified_email
def serve_file(request, run, directory, filename):
    # Get job model instance
    job_model = Job.objects.get(id=run)

    # Check user has permissions to get file
    if job_model.owner != request.user:
        messages.error(request, 'Cannot access this file', extra_tags='alert-danger')
        return redirect(reverse('job_status'))

    # Get file url
    filepath = pathlib.Path(settings.MEDIA_ROOT, 'user_%s' % request.user, 'run_%s' % run, directory, filename)

    return xsendfile(request, filepath)


# TODO: this may fit better somewhere else
def xsendfile(request, filepath):
    if settings.PROD:
        response = HttpResponse()
        response['X-Accel-Redirect'] = filepath.encode('utf-8')
        return response
    else:
        with filepath.open('r') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=%s' % filepath.name
        return response

