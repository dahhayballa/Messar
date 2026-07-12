from django.db import models
from accounts.models import User
from core.models import ServiceType


class Investor(models.Model):
    TYPE_CHOICES = (
        ("PERSON", "Person"),
        ("LOCAL_COMPANY", "Local Company"),
        ("FOREIGN_COMPANY", "Foreign Company"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    full_name = models.CharField(max_length=255)
    nationality = models.CharField(max_length=100)
    national_id = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Project(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name="projects")
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    status = models.CharField(max_length=50, default="DRAFT")

    wilaya = models.CharField(max_length=100, blank=True)
    moughataa = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # قاعدة 5.1: لا يمكن تكرار الاسم داخل نفس النشاط، لكن يمكن
        # تكراره في نشاط مختلف («فندق النجاح» و«وكالة النجاح» معاً)
        unique_together = ("name", "service_type")

    def __str__(self):
        return f"{self.name} ({self.service_type})"


class NameReservation(models.Model):
    class Status(models.TextChoices):
        RESERVED = "RESERVED", "محجوز مؤقتاً"
        CONFIRMED = "CONFIRMED", "مؤكَّد (طلب مُرسَل)"
        REGISTERED = "REGISTERED", "مسجَّل نهائياً (ترخيص صادر)"
        EXPIRED = "EXPIRED", "منتهي الصلاحية"

    name = models.CharField(max_length=255)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    # === إضافة: ربط مباشر بالمشروع، ضروري لتحرير الاسم عند الرفض النهائي ===
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name="name_reservation"
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RESERVED)
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.get_status_display()}"
