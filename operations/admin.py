from django.contrib import admin
from .models import Inspection, Payment, License


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("project", "inspector", "status", "result", "created_at")
    list_filter = ("status", "result")
    search_fields = ("project__name",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("project", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("project__name",)


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("license_number", "project", "type", "issued_at", "expires_at")
    list_filter = ("type",)
    search_fields = ("license_number", "project__name")
