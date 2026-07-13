from rest_framework import serializers
from core.models import ServiceType
from .models import Investor, Project, NameReservation


class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = ["id", "type", "full_name", "nationality", "national_id"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id", "service_type", "name", "status",
            "wilaya", "moughataa", "address", "latitude", "longitude", "created_at",
        ]
        read_only_fields = ["status", "created_at"]


class NameReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NameReservation
        fields = ["id", "name", "service_type", "status", "expires_at", "created_at"]


class OnboardingSerializer(serializers.Serializer):
    """
    يجمع بيانات المرحلة 4 من الرحلة (تسجيل + ملف مستثمر + حجز الاسم)
    في طلب واحد، تُنفَّذ عبر services.create_full_onboarding كـ
    Transaction ذرّية — إما تنجح كل الكيانات معاً أو لا شيء (قاعدة 5.3).
    """
    # بيانات الحساب
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)

    # بيانات المستثمر
    investor_type = serializers.ChoiceField(choices=Investor.TYPE_CHOICES)
    full_name = serializers.CharField(max_length=255)
    nationality = serializers.CharField(max_length=100)
    national_id = serializers.CharField(max_length=100)

    project_name = serializers.CharField(max_length=255)
    service_type = serializers.PrimaryKeyRelatedField(queryset=ServiceType.objects.all())


class CheckNameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, label="الاسم المقترح")
    service_type = serializers.PrimaryKeyRelatedField(queryset=ServiceType.objects.all(), label="نوع النشاط")


class ProjectLocationSerializer(serializers.ModelSerializer):
    """الفصل الخامس: تحديد موقع المشروع بعد إنشائه."""

    class Meta:
        model = Project
        fields = ["wilaya", "moughataa", "address", "latitude", "longitude"]


class NewProjectSerializer(serializers.Serializer):
    """
    الفصل الأخير («مَسار يعرف أحمد»): مستثمر مسجَّل مسبقاً يضيف مشروعاً
    جديداً بلا إعادة تسجيل — يتخطى بيانات الحساب والهوية بالكامل.
    """
    project_name = serializers.CharField(max_length=255)
    service_type = serializers.PrimaryKeyRelatedField(queryset=ServiceType.objects.all())
