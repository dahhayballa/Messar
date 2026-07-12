from django.db import models
from projects.models import Project
from core.models import Requirement


class Application(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "مسودة"
        SUBMITTED = "SUBMITTED", "تم الإرسال"
        UNDER_REVIEW = "UNDER_REVIEW", "قيد المراجعة الإدارية"
        NEEDS_CORRECTION = "NEEDS_CORRECTION", "بحاجة لتصحيح"
        INSPECTION_SCHEDULED = "INSPECTION_SCHEDULED", "بانتظار المعاينة"
        INSPECTION_DONE = "INSPECTION_DONE", "تمت المعاينة"
        # === الدفع يأتي بعد المعاينة الناجحة، لا قبلها ===
        PAYMENT_PENDING = "PAYMENT_PENDING", "بانتظار رفع المخالصة"
        PAYMENT_VERIFIED = "PAYMENT_VERIFIED", "تم تأكيد المخالصة"
        PROVISIONAL_LICENSE = "PROVISIONAL_LICENSE", "ترخيص أولي/مؤقت"
        FOLLOWUP_INSPECTIONS = "FOLLOWUP_INSPECTIONS", "تفتيشات متكررة"
        FINAL_LICENSE = "FINAL_LICENSE", "ترخيص نهائي صادر"
        REJECTED = "REJECTED", "مرفوض نهائياً"

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="application")
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)

    # عدّاد التفتيش الفعلي — يُقارَن بـ project.service_type.required_inspections_count
    completed_inspections_count = models.PositiveSmallIntegerField(default=0)

    rejection_reason = models.CharField(max_length=255, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def inspections_complete(self) -> bool:
        return self.completed_inspections_count >= self.project.service_type.required_inspections_count

    def __str__(self):
        return f"{self.project.name} — {self.get_status_display()}"


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "قيد المراجعة"
        APPROVED = "APPROVED", "مقبولة"
        REJECTED = "REJECTED", "مرفوضة"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE)

    file = models.FileField(upload_to="documents/%Y/%m/")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.CharField(max_length=255, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "requirement")

    def __str__(self):
        return f"{self.requirement} — {self.get_status_display()}"


class StatusHistory(models.Model):
    """كل انتقال حالة — يبني الخط الزمني للمستثمر تلقائياً."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=25, blank=True)
    to_status = models.CharField(max_length=25)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
