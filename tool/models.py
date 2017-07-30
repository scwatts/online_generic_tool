from django.db import models
from django.contrib.auth.models import User


class Job(models.Model):
    job_name = models.CharField()
    owner = models.ForeignKey(User, unique=True)
    status = models.CharField()
    input_file_name = model.CharField()
    input_file = model.FileField()
