from django.db import models
from django.conf import settings


# TODO: this probably fits better somewhere else
def user_run_input_directory(instance, filename):
    return 'user_%s/run_%s/input/%s' % (instance.owner, instance.id, filename)


class Job(models.Model):

    job_name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32)
    input_file = models.FileField(upload_to=user_run_input_directory)
    output_dir = models.FileField()

    # TODO: determine length of redis ids
    redis_id = models.CharField(max_length=255)
    job_queue = models.CharField(max_length=255)


class JobParameters(models.Model):

    job = models.OneToOneField(Job, on_delete=models.CASCADE)

    addgenes = models.BooleanField(default=False)
    addmrna = models.BooleanField(default=False)
    locustag = models.CharField(max_length=32, null=True, blank=True)
    increment = models.CharField(max_length=32, null=True, blank=True)
    gffver = models.CharField(max_length=32, null=True, blank=True)
    compliant = models.BooleanField(default=False)
    centre = models.CharField(max_length=32, null=True, blank=True)
    accver = models.CharField(max_length=32, null=True, blank=True)

    genus = models.CharField(max_length=32, null=True, blank=True)
    species = models.CharField(max_length=32, null=True, blank=True)
    strain = models.CharField(max_length=32, null=True, blank=True)
    plasmid = models.CharField(max_length=32, null=True, blank=True)

    kingdom = models.CharField(max_length=32, null=True, blank=True)
    gcode = models.CharField(max_length=32, null=True, blank=True)
    gram = models.CharField(max_length=32, null=True, blank=True)
    usegenus = models.BooleanField(default=False)
    proteins = models.CharField(max_length=32, null=True, blank=True)
    hmms = models.CharField(max_length=32, null=True, blank=True)
    metagenome = models.BooleanField(default=False)
    rawproduct = models.BooleanField(default=False)
    cdsrnaolap = models.BooleanField(default=False)

    fast = models.BooleanField(default=False)
    noanno = models.BooleanField(default=False)
    mincontig_length = models.CharField(max_length=32, null=True, blank=True)
    evalue = models.CharField(max_length=32, null=True, blank=True)
    rfam = models.CharField(max_length=32, null=True, blank=True)
    norrna = models.BooleanField(default=False)
    notrna = models.BooleanField(default=False)
    rnammer = models.BooleanField(default=False)
