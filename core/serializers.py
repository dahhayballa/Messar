from rest_framework import serializers
from .models import ServiceType, Requirement


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = ["id", "name", "required"]


class ServiceTypeSerializer(serializers.ModelSerializer):
    requirements = RequirementSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceType
        fields = [
            "id", "name", "required_inspections_count",
            "provisional_validity_days", "requirements",
        ]
