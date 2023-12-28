from django.contrib.auth.models import AbstractUser
from django.db import models
from modules.models import FeaturePerms

class AuthUser(AbstractUser):
    email = models.EmailField('Email address', null=True)
    modules = models.CharField(
        'Accessable Modules',
        max_length=250,
        default=0)
    is_admin = models.BooleanField(default=False, null=True)
    feature_perms = models.ManyToManyField(FeaturePerms)
