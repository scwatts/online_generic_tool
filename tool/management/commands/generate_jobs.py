from django.core.management.base import BaseCommand
from django.conf import settings

from tool.models import Job, JobParameters
import tool.queueing


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Data
        data = {'user1':
                    [
                        {'job_name': 'user1_first', 'owner_id': 1},
                        {'job_name': 'user1_second', 'owner_id': 1},
                        {'job_name': 'user1_third', 'owner_id': 1}
                    ],
                'user2': [
                        {'job_name': 'user2_first', 'owner_id': 2},
                        {'job_name': 'user2_second', 'owner_id': 2},
                        {'job_name': 'user2_third', 'owner_id': 2}
                    ],
                'user3':
                    [
                        {'job_name': 'user3_first', 'owner_id': 3}
                    ]
                }

        # Populate with data
        for user, details_list in data.items():
            for details in details_list:
                job_model = Job()
                job_model.job_name = details['job_name']
                job_model.owner_id = details['owner_id']

                job_model.status = 'submitted'
                job_model.input_file = 'some/file/path'
                job_model.job_queue = 'blocked'
                job_model.save()

                # Create job parameter
                job_para_model = JobParameters()
                job_para_model.job = job_model
                job_para_model.save()
                job_model.save()

                # Queue the job
                redis_job = tool.queueing.enqueue(tool.queueing.submit_job, job_model)

                # Save job id and queue to SQL database
                job_model.redis_id = redis_job.get_id()
                job_model.job_queue = settings.REDIS_QUEUE_BLOCKED
                job_model.save()
