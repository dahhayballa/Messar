from django.contrib import admin
from .models import ServiceType, Requirement


class RequirementInline(admin.TabularInline):
    """يسمح بإضافة وثائق النشاط مباشرة من نفس صفحة ServiceType — أسرع للاختبار."""
    model = Requirement
    extra = 1


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "required_inspections_count", "provisional_validity_days")
    inlines = [RequirementInline]


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ("name", "service_type", "required")
    list_filter = ("service_type", "required")
