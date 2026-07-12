from rest_framework import serializers
from .models import Application, Document, StatusHistory


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "project", "requirement", "file", "status", "rejection_reason", "uploaded_at"]
        read_only_fields = ["status", "rejection_reason", "uploaded_at"]


class StatusHistorySerializer(serializers.ModelSerializer):
    to_status_display = serializers.CharField(source="get_to_status_display", read_only=True)

    class Meta:
        model = StatusHistory
        fields = ["from_status", "to_status", "to_status_display", "note", "created_at"]


class ApplicationStatusSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    history = StatusHistorySerializer(many=True, read_only=True)
    required_inspections_count = serializers.IntegerField(
        source="project.service_type.required_inspections_count", read_only=True
    )

    class Meta:
        model = Application
        fields = [
            "id", "status", "status_display", "completed_inspections_count",
            "required_inspections_count", "rejection_reason", "submitted_at",
            "updated_at", "history",
        ]
