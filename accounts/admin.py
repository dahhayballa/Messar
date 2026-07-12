from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class MasarUserAdmin(UserAdmin):
    """
    يوسّع UserAdmin الافتراضي ليعرض phone وrole في القائمة والنموذج،
    بدل الاكتفاء بحقول Django القياسية فقط.
    """
    list_display = ("username", "email", "phone", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("بيانات مَسار", {"fields": ("phone", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("بيانات مَسار", {"fields": ("phone", "role")}),
    )
