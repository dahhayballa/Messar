from django.contrib import admin
from .models import Investor, Project, NameReservation


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "type", "nationality", "user")
    list_filter = ("type", "nationality")
    search_fields = ("full_name", "national_id", "user__email")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "service_type", "investor", "status", "wilaya", "created_at")
    list_filter = ("service_type", "status", "wilaya")
    search_fields = ("name", "investor__full_name")


@admin.register(NameReservation)
class NameReservationAdmin(admin.ModelAdmin):
    list_display = ("name", "service_type", "status", "expires_at", "investor")
    list_filter = ("status", "service_type")
    search_fields = ("name",)
