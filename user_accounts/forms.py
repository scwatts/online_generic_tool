import datetime
import hashlib
import os

from django.utils import timezone
from django.core.mail import send_mail
from django.template import loader
from django.db import models
from django import forms, urls
from django.shortcuts import get_object_or_404

from .models import User, Profile
from django.contrib.auth.forms import UserCreationForm, UsernameField


class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField(label="Email", max_length=254)

    field_order = ('username', 'first_name', 'last_name', 'email')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')
        field_classes = {'username': UsernameField}

    def save(self, commit=True, request=None):
        # Initialise new user from model
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        # Generate verification token and commit to database
        profile = Profile()
        profile.user = user
        profile.unverified_email = self.cleaned_data['email']
        profile.verification_token = hashlib.sha256(os.urandom(512)).hexdigest()[:32]
        profile.token_expiration = timezone.now() + datetime.timedelta(minutes=20)

        if commit:
            profile.save()

        # After successful commit transcation, email user verification token
        # TODO: would this fit better somewhere else?
        context = {
                'email': profile.unverified_email,
                'domain': request.get_host(),
                'site_name': request.get_host(),
                'user': user,
                'token': profile.verification_token
                }

        subject = '%s verification code' % request.get_host()
        body = loader.render_to_string('register/email.html', context)

        # TODO: make bounce address more flexible
        send_mail(subject, body, 'inbox@stephen.ac', [profile.unverified_email], fail_silently=False)

        return user


class EmailChangeForm(forms.Form):

    email = forms.EmailField(label="Email", max_length=254)

    error_messages = {
        'email_exists': 'This email is already in use'
    }


    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super(EmailChangeForm, self).__init__(*args, **kwargs)


    def clean(self):
        # Call parent implementation
        super(EmailChangeForm, self).clean()

        # Email must not be in use
        matching_emails = User.objects.filter(email=self.cleaned_data['email']).values('email')
        if matching_emails:
            raise forms.ValidationError(self.error_messages['email_exists'], code='email_exists')


    def save(self):
        # Get user profile
        profile = get_object_or_404(Profile, user=self.request.user)

        # Update profile with unverified email and associate verification token
        profile.unverified_email = self.cleaned_data['email']
        profile.verification_token = hashlib.sha256(os.urandom(512)).hexdigest()[:32]
        profile.token_expiration = timezone.now() + datetime.timedelta(minutes=20)
        profile.save()

        # Send verification token to new email
        context = {
                'email': profile.unverified_email,
                'domain': self.request.get_host(),
                'site_name': self.request.get_host(),
                'user': self.request.user,
                'token': profile.verification_token
                }

        subject = '%s verification code' % self.request.get_host()
        body = loader.render_to_string('email/change_email.html', context)

        # TODO: make bounce address more flexible
        send_mail(subject, body, 'inbox@stephen.ac', [profile.unverified_email], fail_silently=False)
