from rest_framework import serializers
from .models import Inspection, Payment, License


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = ["id", "project", "inspector", "status", "result", "notes", "created_at"]
        read_only_fields = ["status", "created_at"]


class InspectionReportSerializer(serializers.Serializer):
    """
    ما يرسله تطبيق المفتش فعلياً بعد الزيارة (الفصل الثامن):
    نتيجة + ملاحظات، لا حقول الإنشاء الأولية.
    """
    result = serializers.ChoiceField(choices=[("PASSED", "مطابقة"), ("FAILED", "غير مطابقة")])
    notes = serializers.CharField(required=False, allow_blank=True)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "project", "amount", "receipt", "status", "created_at"]
        read_only_fields = ["status", "created_at"]


class LicenseSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = License
        fields = ["id", "project", "type", "type_display", "license_number", "issued_at", "expires_at"]
