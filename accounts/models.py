from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('INVESTOR', 'Investor'),
        ('ADMIN', 'Admin'),
        ('INSPECTOR', 'Inspector'),
    )

    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='INVESTOR')