from django.db import models

# Create your models here.
from django.db import models
from projects.models import Project
from accounts.models import User

class Inspection(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    status = models.CharField(max_length=20, default='PENDING')
    result = models.CharField(max_length=20, null=True, blank=True)

    notes = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    checklist_completed = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='inspections/%Y/%m/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)



class Payment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.FileField(upload_to='payments/')
    status = models.CharField(max_length=20, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)


class License(models.Model):
    TYPE_CHOICES = (
        ('INITIAL', 'Initial'),
        ('FINAL', 'Final'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    license_number = models.CharField(max_length=100)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()