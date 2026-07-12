import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from workflow.models import Application
from workflow.services import change_status, record_inspection_result
from .models import Inspection, License, Payment


def generate_license_number(project) -> str:
    """رقم ترخيص فريد وقابل للتحقق العلني — نمط بسيط لكن كافٍ للـMVP."""
    year = timezone.now().year
    short_id = uuid.uuid4().hex[:6].upper()
    return f"MSR-{year}-{project.service_type_id}-{short_id}"


@transaction.atomic
def submit_inspection_report(inspection: Inspection, result: str, notes: str = "") -> Application:
    """
    الفصل الثامن: المفتش يرسل تقريره. يحدّث Inspection ثم يُشغّل منطق
    workflow.record_inspection_result المسؤول عن قرار الحالة التالية.
    """
    inspection.result = result
    inspection.status = "DONE"
    inspection.notes = notes
    inspection.save(update_fields=["result", "status", "notes"])

    application = Application.objects.get(project=inspection.project)
    passed = result == "PASSED"
    application = record_inspection_result(application, passed=passed)

    # اكتمل عدد التفتيشات المطلوب فعلياً؟ أصدر الترخيص النهائي الآن
    if application.status == Application.Status.FINAL_LICENSE:
        License.objects.create(
            project=application.project, type="FINAL",
            license_number=generate_license_number(application.project),
            expires_at=timezone.now() + timedelta(days=365 * 3),  # صلاحية افتراضية 3 سنوات
        )

    return application


@transaction.atomic
def verify_payment(payment: Payment) -> Application:
    """
    الفصل التاسع: الإدارة تؤكد صحة المخالصة المرفوعة، فيصدر الترخيص
    الأولي/المؤقت مباشرة (الفصل العاشر) بمدة صلاحية نوع النشاط.
    """
    payment.status = "VERIFIED"
    payment.save(update_fields=["status"])

    application = Application.objects.get(project=payment.project)
    application = change_status(application, Application.Status.PROVISIONAL_LICENSE, note="تأكيد المخالصة")

    validity_days = application.project.service_type.provisional_validity_days
    License.objects.create(
        project=application.project, type="INITIAL",
        license_number=generate_license_number(application.project),
        expires_at=timezone.now() + timedelta(days=validity_days),
    )

    return application
