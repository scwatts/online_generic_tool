import time


import redis
import rq


from django.core.management.base import BaseCommand
from django.conf import settings
from tool.models import Job


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--interval', action='store', dest='interval',
                type=int, default=2, help='Interval between queuing')


    def handle(self, *args, **options):
        while True:
            # Get jobs by user and total count
            jobs = Job.objects.filter(status='submitted')
            owner_jobs = dict()
            # TODO: investigate the ordering of the jobs; will the oldest job be queued first?
            for job in jobs:
                try:
                    owner_jobs[job.owner].append(job)
                except KeyError:
                    owner_jobs[job.owner] = [job]

            # Get connection to redis so we can retrieve worker info
            redis_connection = redis.Redis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB)

            def worker_on_active_queue(worker):
                queue_names = (q.name for q in worker.queues)
                return settings.REDIS_QUEUE_ACTIVE in queue_names

            # Get the queues
            active_queue = rq.Queue(settings.REDIS_QUEUE_ACTIVE, connection=redis_connection)
            blocked_queue = rq.Queue(settings.REDIS_QUEUE_BLOCKED, connection=redis_connection)

            with rq.Connection(redis_connection):
                # Collect worker information
                workers = [w for w in rq.Worker.all() if worker_on_active_queue(w)]
                idle_worker_count = len([w for w in workers if w.get_state() == 'idle'])

                # TODO: implement limit for total jobs a user can have active
                for owner in owner_jobs:
                    # Only queue job if we have idle workers
                    if idle_worker_count <= 0:
                        break

                    # Get job from this user to queue
                    job_model = owner_jobs[owner].pop(0)

                    # Remove job from blocked queue and add it to active
                    redis_job = blocked_queue.fetch_job(job_model.redis_id)
                    blocked_queue.remove(redis_job)
                    active_queue.enqueue_job(redis_job)

                    # Update job model status and queue
                    job_model.status = 'queued'
                    job_model.queue = settings.REDIS_QUEUE_ACTIVE
                    job_model.save()

                    # Update number of idle workers after a small delay
                    time.sleep(0.05)
                    idle_worker_count = len([w for w in workers if w.get_state() == 'idle'])

            # Loop every couple of minutes
            time.sleep(options['interval'])
