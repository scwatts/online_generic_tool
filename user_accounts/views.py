import datetime
import hashlib
import os

from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from django.contrib import messages

from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views import View

from django.contrib.auth import update_session_auth_hash, get_user_model, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm

from django.core.mail import send_mail

from django.template import loader

from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone

from .forms import CustomUserCreationForm, EmailChangeForm, EmailVerifyForm
from .models import Profile, User


@method_decorator([sensitive_post_parameters(), never_cache], name='dispatch')
class RegisterAccount(View):

    def dispatch(self, request, *args, **kwargs):
        # Redirect if already authenticated
        if request.user.is_authenticated:
            messages.warning(request, 'Unable to register account while logged in', extra_tags='alert-warning')
            return redirect(reverse('home_page'))
        return super(RegisterAccount, self).dispatch(request, *args, **kwargs)


    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            return HttpResponseRedirect(reverse('register_account_done'))
        return render(request, 'register/form.html', {'form': form})


    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'register/form.html', {'form': form})


@method_decorator(never_cache, name='dispatch')
class Logout(View):

    def get(self, request):
        auth_logout(request)
        return redirect(reverse('home_page'))


# TODO: option to send new token
@method_decorator(login_required, name='dispatch')
class EmailVerify(View):

    def get(self, request, *args, **kwargs):
        form = EmailVerifyForm()
        if kwargs.get('token'):
            return self.verify_token(request, form, kwargs.get('token'))

        return render(request, 'email/verify.html', {'form': form})


    def post(self, request, *args, **kwargs):
        form = EmailVerifyForm(data=request.POST)
        if form.is_valid():
            input_token = form.cleaned_data['token']
            return self.verify_token(request, form, input_token)

        return render(request, 'email/verify.html', {'form': form})


    def verify_token(self, request, form, input_token):
        # Get user profile
        profile = get_object_or_404(Profile, user=request.user)

        # In exceptionally rare circumstances, we can get the same user with two accounts attempting to
        # verify a single email address across two accounts. Check for this now.
        matching_emails = User.objects.filter(email=profile.unverified_email).values('email')
        if profile.unverified_email and matching_emails:
            messages.error(request, 'This email address is already in use', extra_tags='alert-warning')
            return render(request, 'email/verify.html', {'form': form})

        # Once we have a token, attempt to verify
        # Ensure the user has not already verified the current address
        if not profile.unverified_email:
            messages.error(request, 'The email associated with this account is already verified', extra_tags='alert-warning')

        # Make sure there is a token to verify against
        elif not profile.verification_token:
            messages.error(request, 'There is no token to verify', extra_tags='alert-danger')

        # Check that the token has not expired
        elif timezone.now() > profile.token_expiration:
            messages.error(request, 'The email verification token has expired', extra_tags='alert-warning')

        # Get the expected verification token and compare with specified
        elif profile.verification_token == input_token:
            request.user.is_verified = True
            request.user.email = profile.unverified_email
            profile.verification_token = ''
            profile.unverified_email = ''
            profile.token_expiration = datetime.datetime.utcfromtimestamp(0)
            request.user.save()
            profile.save()
            messages.success(request, 'Your account has been verified', extra_tags='alert-success')
        else:
            messages.error(request, 'Could not verify your email', extra_tags='alert-danger')

        return render(request, 'email/verify.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ResendVerification(View):

    def get(self, request):
        # Get user profile
        profile = get_object_or_404(Profile, user=request.user)

        # Check that the user has an unverified email to verify
        if not profile.unverified_email:
            messages.error(request, 'You don\'t have any email addresses to verify', extra_tags='alert-warning')
            return redirect(reverse('email_verify'))


        # TODO: can we refactor this into a function (similar blocks in forms.py)
        # Generate new token and send email
        profile.verification_token = hashlib.sha256(os.urandom(512)).hexdigest()[:32]
        profile.token_expiration = timezone.now() + datetime.timedelta(minutes=20)
        profile.save()

        context = {
                'email': profile.unverified_email,
                'domain': request.get_host(),
                'site_name': request.get_host(),
                'user': request.user,
                'token': profile.verification_token
                }

        subject = '%s verification code' % request.get_host()
        body = loader.render_to_string('register/email.html', context)

        # TODO: make bounce address more flexible
        send_mail(subject, body, 'inbox@stephen.ac', [profile.unverified_email], fail_silently=False)

        messages.success(request, 'Resent verification code', extra_tags='alert-success')
        return redirect(reverse('email_verify'))


@method_decorator(login_required, name='dispatch')
class EmailChange(View):

    def post(self, request):
        form = EmailChangeForm(request=request, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Added a new unverified email', extra_tags='alert-success')
            msg = 'An email has been sent with instructions to complete verification of your new email'
            messages.warning(request, msg, extra_tags='alert-warning')

        return render(request, 'email/change_form.html', {'form': form, 'title': 'Email change'})


    def get(self, request):
        form = EmailChangeForm(request=request)
        return render(request, 'email/change_form.html', {'form': form, 'title': 'Email change'})


@method_decorator([login_required, sensitive_post_parameters()], name='dispatch')
class PasswordChange(View):

    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Updating the password logs out all other sessions for the user
            # except the current one.
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password has been updated', extra_tags='alert-success')

        return render(request, 'password/change_form.html', {'form': form, 'title': 'Password change'})


    def get(self, request):
        form = PasswordChangeForm(user=request.user)
        return render(request, 'password/change_form.html', {'form': form, 'title': 'Password change'})


class PasswordReset(View):

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': default_token_generator,
                # Leaving to be set in form
                'from_email': None,
                'email_template_name': 'password/reset_email.html',
                'subject_template_name': 'password/reset_email_subject.txt',
                'request': request,
                'html_email_template_name': None,
            }
            form.save(**opts)
            msg = '''We've emailed you instructions for setting your password, if an account exists
                     with the email you entered'''
            messages.success(request, msg, extra_tags='alert-success')

        return render(request, 'password/reset_form.html', {'form': form, 'title': 'Password reset'})


    def get(self, request):
        form = PasswordResetForm()
        return render(request, 'password/reset_form.html', {'form': form, 'title': 'Password reset'})


@method_decorator([sensitive_post_parameters(), never_cache], name='dispatch')
class PasswordResetConfirm(View):

    def dispatch(self, request, token, uidb64, *args, **kwargs):
        UserModel = get_user_model()
        assert uidb64 is not None and token is not None  # checked by URLconf

        try:
            # urlsafe_base64_decode() decodes to bytestring on Python 3
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            return super(PasswordResetConfirm, self).dispatch(request, user, *args, **kwargs)

        title = 'Password reset unsuccessful'
        context = {'form': None, 'title': title, 'validlink': None}
        return render(request, 'password/reset_confirm.html', context)


    def post(self, request, user):
        title = 'Enter new password'
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changes successfully', extra_tags='alert-success')
            return redirect(reverse('home_page'))

        context = {'form': form, 'title': title, 'validlink': True}
        return render(request, 'password/reset_confirm.html', context)


    def get(self, request, user):
        form = SetPasswordForm(user)
        title = 'Enter new password'
        context = {'form': form, 'title': title, 'validlink': True}
        return render(request, 'password/reset_confirm.html', context)


@method_decorator(login_required, name='dispatch')
class Account(View):

    def get(self, request):
        return render(request, 'account/home.html')
