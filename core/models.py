from django.db import models


class ServiceType(models.Model):
    name = models.CharField(max_length=100)

    # === إضافة ضرورية: بدونها لا يمكن معرفة متى يصدر الترخيص النهائي ===
    required_inspections_count = models.PositiveSmallIntegerField(
        default=1,
        help_text="عدد التفتيشات الناجحة المطلوبة قبل إصدار الترخيص النهائي لهذا النشاط",
    )
    provisional_validity_days = models.PositiveIntegerField(
        default=180, help_text="مدة صلاحية الترخيص الأولي بالأيام (افتراضياً 6 أشهر)"
    )

    def __str__(self):
        return self.name


class Requirement(models.Model):
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="requirements")
    name = models.CharField(max_length=255)
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.service_type})"
