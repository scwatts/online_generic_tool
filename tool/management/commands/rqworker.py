import os


from redis import Redis
from rq import Connection, Worker


from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--pid', action='store', dest='pid',
                            default=None, help='PID file to write the worker`s pid into')
        parser.add_argument('--queues', nargs='*', type=str,
                            help='The queues to work on, separated by space')


    def handle(self, *args, **options):
        pid = options.get('pid')
        if pid:
            with open(os.path.expanduser(pid), "w") as fp:
                fp.write(str(os.getpid()))

        if options['queues']:
            queues = options['queues']
        else:
            queues = [settings.REDIS_QUEUE_ACTIVE]

        # Get connection and do work
        redis_connection = Redis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)
        with Connection(redis_connection):
            worker = Worker(queues)
            worker.work()
