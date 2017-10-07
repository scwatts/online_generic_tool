import pathlib
import subprocess


from rq import Queue
from redis import Redis


from django.conf import settings
from django.utils import timezone

from tool.models import Job


def enqueue(function, *args, **kwargs):
    redis_connection = Redis(host=settings.REDIS_HOST,
                             port=settings.REDIS_PORT,
                             db=settings.REDIS_DB)
    queue = Queue(settings.REDIS_QUEUE_BLOCKED, connection=redis_connection)

    return queue.enqueue(function, *args, timeout=settings.JOB_TIMEOUT, **kwargs)


def execute_job(job_id):
    # Get the job instance
    job_instance = Job.objects.get(id=job_id)

    # Set job queue to active in SQL database
    job_instance.job_queue = settings.REDIS_QUEUE_ACTIVE

    # Collect parameters and format to string
    # TODO: consider whether this is secure enough
    # TODO: is there a more efficient way to do this?
    param_instance = job_instance.jobparameters
    param_fields = param_instance._meta.get_fields()[2:]
    param_gen = ((f.attname, f.value_from_object(param_instance)) for f in param_fields)
    params_str = ' '.join(['--%s %s' % (fn, fv) for fn, fv in param_gen if fv])

    # Add output directory and prefix to entry and parameter string
    job_instance.run_dir.name = 'user_%s/run_%s/' % (job_instance.owner, job_instance.id)
    output_dir = pathlib.Path(job_instance.run_dir.path, 'output')
    prefix = pathlib.Path(job_instance.input_file.name).stem
    params_str = '%s --outdir %s --prefix %s' % (params_str, output_dir, prefix)

    # Finialise command
    binary = settings.ENTRY_POINT
    cmd_template = '%s %s %s'
    cmd = cmd_template % (binary, params_str, job_instance.input_file.path)

    # Update job status to running and execute command
    job_instance.status = 'running'
    job_instance.save()
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check process return code
    if p.returncode != 0:
        job_instance.status = 'failed'
    else:
        job_instance.status = 'completed'
        job_instance.job_queue = ''
        job_instance.redis_id = ''
    job_instance.duration = timezone.now() - job_instance.start_time
    job_instance.save()
