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
    progress_percentage = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "status", "status_display", "completed_inspections_count",
            "required_inspections_count", "rejection_reason", "submitted_at",
            "updated_at", "history", "progress_percentage",
        ]

    def get_progress_percentage(self, obj) -> float:
        # Calcule le pourcentage des documents requis soumis non rejetés
        project = obj.project
        mandatory_reqs = project.service_type.requirements.filter(required=True)
        total_mandatory = mandatory_reqs.count()
        if total_mandatory == 0:
            return 100.0

        uploaded_mandatory_count = Document.objects.filter(
            project=project,
            requirement__in=mandatory_reqs
        ).exclude(status=Document.Status.REJECTED).count()

        return round((uploaded_mandatory_count / total_mandatory) * 100.0, 2)


class DocumentReviewSerializer(serializers.Serializer):
    """الفصل السابع: مراجعة وثيقة واحدة — قبول أو رفض بسبب واضح."""
    approved = serializers.BooleanField()
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data["approved"] and not data.get("rejection_reason"):
            raise serializers.ValidationError("سبب الرفض إلزامي عند رفض وثيقة.")
        return data
