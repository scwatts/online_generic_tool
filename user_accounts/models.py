from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # Set first name, last name, and email to be required for registeration
    # Also require email to be unique among all users
    first_name = models.CharField('first name', max_length=30)
    last_name = models.CharField('last name', max_length=150)
    email = models.EmailField('email address', unique=True)

    # Status of email verification
    is_verified = models.BooleanField(
        ('verified'),
        default=False,
        help_text=(
            'Designates whether this user has verified their email. '
        ),
    )


class Profile(models.Model):
    # Link to django auth User model
    user = models.OneToOneField(User, related_name='profile')

    # Email address
    unverified_email = models.EmailField('unverified email address', unique=True, blank=True)

    # Fields for email verification via token
    verification_token = models.CharField('verification token', max_length=32)
    token_expiration = models.DateTimeField()
