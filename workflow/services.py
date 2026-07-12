from django.db import transaction
from django.utils import timezone

from projects.models import NameReservation
from projects.services import release_name_on_final_rejection
from .models import Application, Document, StatusHistory


def mandatory_documents_complete(project) -> bool:
    """
    قاعدة 5.4: لا يمكن إرسال الطلب قبل اكتمال كل الوثائق الإلزامية
    (المخالصة المالية غير مشمولة هنا — ترفع لاحقاً بعد المعاينة).
    """
    mandatory_ids = set(
        project.service_type.requirements.filter(required=True).values_list("id", flat=True)
    )
    uploaded_ids = set(
        Document.objects.filter(project=project, requirement_id__in=mandatory_ids)
        .exclude(status=Document.Status.REJECTED)
        .values_list("requirement_id", flat=True)
    )
    return mandatory_ids.issubset(uploaded_ids)


@transaction.atomic
def change_status(application: Application, to_status: str, note: str = "") -> Application:
    """يغيّر حالة الطلب ويسجّل الانتقال في StatusHistory دائماً معاً."""
    from_status = application.status
    application.status = to_status
    application.save(update_fields=["status", "updated_at"])
    StatusHistory.objects.create(
        application=application, from_status=from_status, to_status=to_status, note=note,
    )

    # قاعدة 5.2: عند الرفض النهائي، يعود اسم المشروع متاحاً تلقائياً
    if to_status == Application.Status.REJECTED:
        release_name_on_final_rejection(application.project)

    # عند الترخيص النهائي، يصبح الاسم "مسجَّلاً نهائياً"
    if to_status == Application.Status.FINAL_LICENSE:
        NameReservation.objects.filter(project=application.project).update(
            status=NameReservation.Status.REGISTERED
        )

    return application


@transaction.atomic
def submit_application(project) -> Application:
    if not mandatory_documents_complete(project):
        raise ValueError("لا يمكن الإرسال قبل اكتمال كل الوثائق الإلزامية.")

    application, _ = Application.objects.get_or_create(project=project)
    application.submitted_at = timezone.now()
    application.save(update_fields=["submitted_at"])
    return change_status(application, Application.Status.SUBMITTED, note="إرسال أول للطلب")


def record_inspection_result(application: Application, passed: bool) -> Application:
    """
    يُستدعى من operations.services بعد كل تفتيش. يطبّق منطق:
    أول نجاح ← ترخيص أولي. النجاحات التالية ← تُحتسب حتى الاكتمال ← ترخيص نهائي.
    """
    if not passed:
        return change_status(application, Application.Status.INSPECTION_SCHEDULED, note="فشل — إعادة جدولة")

    application.completed_inspections_count += 1
    application.save(update_fields=["completed_inspections_count"])

    if application.completed_inspections_count == 1:
        return change_status(application, Application.Status.PAYMENT_PENDING, note="أول معاينة ناجحة")

    if application.inspections_complete:
        return change_status(application, Application.Status.FINAL_LICENSE, note="اكتمل عدد التفتيشات")

    return change_status(application, Application.Status.FOLLOWUP_INSPECTIONS, note="معاينة إضافية ناجحة")
