from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import BuddhiAIUserManager

class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = BuddhiAIUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email