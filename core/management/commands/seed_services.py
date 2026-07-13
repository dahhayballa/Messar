"""
أمر تعبئة تلقائي لكل أنواع الخدمات السياحية الستة ووثائقها،
مبني على procedures.gov.mr والوثائق الرسمية الممسوحة ضوئياً.

الاستخدام:
    python manage.py seed_services

آمن للتكرار (idempotent) — يستخدم get_or_create، لن يُنشئ تكراراً
إن شُغِّل أكثر من مرة.
"""

from django.core.management.base import BaseCommand
from core.models import ServiceType, Requirement


SERVICES = [
    {
        "name": "وكالة سفر",
        "required_inspections_count": 1,
        "provisional_validity_days": 180,
        "requirements": [
            "طلب موجه للوزير المكلف بالسياحة",
            "سجل تجاري",
            "الموقع الجغرافي للوكالة",
            "البطاقات الرمادية للسيارات",
            "مخالصة مالية",
            "نسخة من شهادة الجنسية",
            "عقد إيجار المقر",
            "شهادة تبريز",
            "إفادة بمزاولة المهنة سابقاً",
        ],
    },
    {
        "name": "فنادق ونزل وشقق مفروشة",
        "required_inspections_count": 2,
        "provisional_validity_days": 180,
        "requirements": [
            "طلب موجه للوزير المكلف بالسياحة",
            "سجل تجاري",
            "بيانات اتصال",
            "شهادة تبريز",
            "شهادة مهنية للمسير",
            "دراسة جدوى",
            "النظام الأساسي",
            "رخصة حيازة أو سند ملكية",
            "مخطط الموقع",
            "إثبات القدرة على التمويل",
            "عقد الإيجار (بديل عن الملكية)",
        ],
    },
    {
        "name": "قاعة حفلات",
        "required_inspections_count": 2,
        "provisional_validity_days": 180,
        "requirements": [
            "طلب موجه لوزيرة التجارة والسياحة",
            "بطاقة تعريف وطنية لمقدم الطلب",
            "شهادة تبريز (أقل من 3 أشهر)",
            "سجل تجاري",
            "دراسة جدوى لمشروع قاعة الحفلات",
            "رخصة حيازة أرض أو عقد إيجار (3 سنوات فأكثر)",
            "مخطط هيكلي مفصل للقاعة",
            "مخالصة مالية",
        ],
    },
    {
        "name": "مطعم ومقهى",
        "required_inspections_count": 2,
        "provisional_validity_days": 180,
        "requirements": [
            "سجل تجاري بنشاط مطعمي",
            "بطاقة تعريف المسير",
            "شهادة تبريز أو بحث أخلاقي (أقل من 3 أشهر)",
            "إفادة ملكية أو عقد إيجار المقر",
            "لائحة العمال",
            "مخالصة مالية",
        ],
    },
    {
        "name": "مرشد سياحي",
        "required_inspections_count": 1,
        "provisional_validity_days": 180,
        "requirements": [
            "طلب",
            "مستخرج شهادة ميلاد",
            "سيرة ذاتية",
            "شهادة إقامة",
            "شهادة تبريز (أقل من 3 أشهر)",
        ],
    },
    {
        "name": "طلب قطعة أرض سياحية",
        "required_inspections_count": 1,
        "provisional_validity_days": 180,
        "requirements": [
            "طلب موجه للوزير المكلف بالسياحة",
            "سجل تجاري باسم المشروع",
            "دراسة جدوى",
            "إثبات ضمانات القدرة على تمويل المشروع",
        ],
    },
]


class Command(BaseCommand):
    help = "يُعبّئ قاعدة البيانات بكل أنواع الخدمات السياحية ووثائقها المطلوبة."

    def handle(self, *args, **options):
        for service_data in SERVICES:
            service, created = ServiceType.objects.get_or_create(
                name=service_data["name"],
                defaults={
                    "required_inspections_count": service_data["required_inspections_count"],
                    "provisional_validity_days": service_data["provisional_validity_days"],
                },
            )
            action = "أُنشئ" if created else "موجود مسبقاً"
            self.stdout.write(f"[{action}] {service.name}")

            for req_name in service_data["requirements"]:
                _, req_created = Requirement.objects.get_or_create(
                    service_type=service, name=req_name, defaults={"required": True},
                )
                if req_created:
                    self.stdout.write(f"    + {req_name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nتمت تعبئة {len(SERVICES)} أنواع خدمة بنجاح."
        ))
