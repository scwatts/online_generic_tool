import subprocess


from rq import Queue
from redis import Redis


from django.conf import settings


def enqueue(function, *args, **kwargs):
    redis_connection = Redis(host=settings.REDIS_HOST,
                             port=settings.REDIS_PORT,
                             db=settings.REDIS_DB)
    queue = Queue(connection=redis_connection)

    queue.enqueue(function, *args, **kwargs)


def submit_job(job_instance):
    # Collect parameters and format to string
    # TODO: consider whether this is secure enough
    # TODO: is there a more efficient way to do this?
    param_instance = job_instance.jobparameters
    param_fields = param_instance._meta.get_fields()[2:]
    param_gen = ((f.attname, f.value_from_object(param_instance)) for f in param_fields)
    params_str = ' '.join(['--%s %s' % (fn, fv) for fn, fv in param_gen if fv])

    # Add output directory to entry and parameter string
    job_instance.output_dir.name = 'user_%s/run_%s/output/' % (job_instance.owner, job_instance.id)
    params_str = '%s --outdir %s' % (params_str, job_instance.output_dir.path)

    # Finialise command
    # TEMP: binary
    binary = '/home/stephen/work/development/online_generic_tool/prokka/bin/prokka'
    cmd_template = '%s %s %s'
    cmd = cmd_template % (binary, params_str, job_instance.input_file.path)

    # Update job status to running and execute command
    job_instance.status = 'running'
    job_instance.save()
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check process return code
    if p.returncode != 0:
        job_instance.status = 'failed'
        job_instance.stderr = p.stderr
    else:
        job_instance.status = 'completed'
    job_instance.save()
