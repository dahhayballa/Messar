from django.contrib import admin
from .models import Application, Document, StatusHistory


class StatusHistoryInline(admin.TabularInline):
    """الخط الزمني الكامل مباشرة تحت الطلب — أسرع وسيلة للتحقق من التتبع."""
    model = StatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "note", "created_at")
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("project", "status", "completed_inspections_count", "submitted_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("project__name",)
    inlines = [StatusHistoryInline]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("requirement", "project", "status", "uploaded_at")
    list_filter = ("status", "requirement")
    search_fields = ("project__name",)
