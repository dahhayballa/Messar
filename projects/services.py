"""
طبقة الخدمات (Services Layer) — المنطق الذي لا ينتمي لـview بسيط ولا
لنموذج، بل يُنسّق بين عدة تطبيقات (accounts + core + projects).
"""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from accounts.models import User
from core.models import ServiceType
from .models import Investor, NameReservation, Project

RESERVATION_DAYS = 7  # قاعدة 5.2 في دفتر الالتزامات


def is_name_available(name: str, service_type: ServiceType) -> bool:
    """
    التحقق من توفر الاسم لنشاط محدد (قاعدة 5.1):
    - الاسم مرتبط بنوع النشاط، يمكن تكراره في نشاط مختلف
    - لا يُعتبر مستخدَماً إن كان الحجز القديم منتهي الصلاحية
    """
    active_reservation = (
        NameReservation.objects.filter(name__iexact=name, service_type=service_type)
        .exclude(status=NameReservation.Status.EXPIRED)
        .first()
    )
    if not active_reservation:
        return True
    if active_reservation.status == NameReservation.Status.RESERVED and active_reservation.expires_at < timezone.now():
        # منتهي فعلياً لكن لم تُحدَّث حالته بعد — يُعامَل كمتاح
        return True
    return False


@transaction.atomic
def create_full_onboarding(*, email, phone, password, investor_type,
                             full_name, nationality, national_id,
                             project_name, service_type: ServiceType) -> Project:
    """
    ينفّذ المرحلة 4 من الرحلة بالكامل في عملية ذرّية واحدة (قاعدة 5.3):
    User → Investor → NameReservation → Project
    إن فشلت أي خطوة، تُلغى كل الخطوات السابقة تلقائياً (transaction.atomic).
    """
    if not is_name_available(project_name, service_type):
        raise ValueError(f"الاسم «{project_name}» مستخدم بالفعل لنشاط «{service_type}»")

    user = User.objects.create_user(
        username=email, email=email, phone=phone, password=password, role="INVESTOR",
    )

    investor = Investor.objects.create(
        user=user, type=investor_type, full_name=full_name,
        nationality=nationality, national_id=national_id,
    )

    project = Project.objects.create(
        investor=investor, service_type=service_type, name=project_name, status="DRAFT",
        wilaya="", moughataa="", address="",
    )

    NameReservation.objects.create(
        name=project_name, service_type=service_type, investor=investor,
        status=NameReservation.Status.RESERVED,
        expires_at=timezone.now() + timedelta(days=RESERVATION_DAYS),
        project=project,
    )

    return project


def release_name_on_final_rejection(project: Project) -> None:
    """
    قاعدة 5.2: إن رُفض الطلب رفضاً نهائياً، يعود الاسم متاحاً للجميع.
    تُستدعى من workflow عند الانتقال إلى status=REJECTED نهائياً.
    """
    NameReservation.objects.filter(project=project).update(
        status=NameReservation.Status.EXPIRED
    )


@transaction.atomic
def create_project_for_existing_investor(*, investor: Investor, project_name: str, service_type: ServiceType) -> Project:
    """
    Permet à un investisseur existant de créer un nouveau projet et de réserver son nom (Chapitre Final).
    Processus atomique : vérification du nom -> création du projet -> création de la réservation de nom (RESERVED pour 7 jours).
    """
    if not is_name_available(project_name, service_type):
        raise ValueError(f"الاسم «{project_name}» مستخدم بالفعل لنشاط «{service_type}»")

    project = Project.objects.create(
        investor=investor, service_type=service_type, name=project_name, status="DRAFT",
        wilaya="", moughataa="", address="",
    )

    NameReservation.objects.create(
        name=project_name, service_type=service_type, investor=investor,
        status=NameReservation.Status.RESERVED,
        expires_at=timezone.now() + timedelta(days=RESERVATION_DAYS),
        project=project,
    )

    return project

