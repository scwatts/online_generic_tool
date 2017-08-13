from django import forms

from .models import Job, JobParameters


class JobSubmissionForm(forms.ModelForm):

    job_name = forms.CharField(max_length=32)
    input_file = forms.FileField()

    field_order = ('job_name', 'input_file', 'genus', 'species', 'strain', 'plasmid', 'kingdom', 'metagenome')

    class Meta:
        model = JobParameters
        fields = ('job_name', 'input_file', 'genus', 'species', 'strain', 'plasmid', 'kingdom', 'metagenome')


    def save(self, request, commit=True):
        # Init new job models
        job = Job()
        job_parameters = super().save(commit=False)

        # Populate job data and save
        job.job_name = self.cleaned_data['job_name']
        job.owner = request.user
        # TODO: should this be a predefined choice?
        job.status = 'submitted'
        job.input_file = self.cleaned_data['input_file']

        # We want to save the input file in a directory under run_${instance_id} but to get the
        # instance id the model must first be commited to the database. So we commit the model to
        # database without the input file, and make a second commit with file and the instance id
        # that we now have
        input_file, job.input_file = job.input_file, None
        job.save()
        job.input_file = input_file
        job.save()

        # Set job field in parameter model, then save
        job_parameters.job = job
        job_parameters.save()

        return job
