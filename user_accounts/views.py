import datetime
import hashlib
import os

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from django.contrib import messages

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, get_user_model, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm, AuthenticationForm

from django.core.mail import send_mail

from django.template import loader

from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone

from .forms import CustomUserCreationForm, EmailChangeForm, EmailVerifyForm
from .models import Profile
from .decorators import requires_verified_email


@sensitive_post_parameters()
@csrf_protect
@never_cache
def register_account(request):
    # Redirect if already authenticated
    if request.user.is_authenticated:
        messages.warning(request, 'Unable to register account while logged in', extra_tags='alert-warning')
        return redirect(reverse('home_page'))

    # If we're recieving data then process, else present form
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(request=request)
            return HttpResponseRedirect(reverse('register_account_done'))
    else:
        form = CustomUserCreationForm()

    return render(request, 'register/form.html', {'form': form})


@never_cache
def logout(request):
    auth_logout(request)
    return redirect(reverse('home_page'))


# TODO: option to send new token
@login_required
def email_verify(request, token=None):
    # Get user profile
    profile = get_object_or_404(Profile, user=request.user)

    # Attempt to get a token from user
    if token:
        input_token = token
        form = EmailVerifyForm()
    else:
        if request.method == 'POST':
            form = EmailVerifyForm(data=request.POST)
            if form.is_valid():
                input_token = form.cleaned_data['token']
        else:
            form = EmailVerifyForm()
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


@login_required
def resend_verification(request):
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


@csrf_protect
@login_required
def email_change(request):
    # If we're recieving data then process, else present form
    if request.method == "POST":
        form = EmailChangeForm(request=request, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Added a new unverified email', extra_tags='alert-success')
            msg = 'An email has been sent with instructions to complete verification of your new email'
            messages.warning(request, msg, extra_tags='alert-warning')
    else:
        form = EmailChangeForm(request=request)

    context = {
        'form': form,
        'title': 'Email change',
    }

    return render(request, 'email/change_form.html', context)



@sensitive_post_parameters()
@csrf_protect
@login_required
def password_change(request):
    # If we're recieving data then process, else present form
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Updating the password logs out all other sessions for the user
            # except the current one.
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password has been updated', extra_tags='alert-success')
    else:
        form = PasswordChangeForm(user=request.user)

    context = {
        'form': form,
        'title': 'Password change',
    }

    return render(request, 'password/change_form.html', context)


@csrf_protect
def password_reset(request):
    # If we're recieving data then process, else present form
    if request.method == "POST":
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
    else:
        form = PasswordResetForm()

    context = {
        'form': form,
        'title': 'Password reset',
    }

    return render(request, 'password/reset_form.html', context)


@sensitive_post_parameters()
@never_cache
def password_reset_confirm(request, uidb64=None, token=None):
    UserModel = get_user_model()
    assert uidb64 is not None and token is not None  # checked by URLconf

    try:
        # urlsafe_base64_decode() decodes to bytestring on Python 3
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
        title = 'Enter new password'
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Password changes successfully', extra_tags='alert-success')
                return redirect(reverse('home_page'))
        else:
            form = SetPasswordForm(user)
    else:
        validlink = False
        form = None
        title = 'Password reset unsuccessful'

    context = {
        'form': form,
        'title': title,
        'validlink': validlink,
    }

    return render(request, 'password/reset_confirm.html', context)


@login_required
def account(request):
    return render(request, 'account/home.html')
