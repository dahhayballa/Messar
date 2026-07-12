from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from projects.models import Project
from .models import Application, Document
from .serializers import ApplicationStatusSerializer, DocumentSerializer
from .services import submit_application


class IsProjectOwner(permissions.BasePermission):
    """المستثمر يرى ويعدّل وثائق/طلبات مشاريعه هو فقط."""

    def has_object_permission(self, request, view, obj):
        project = obj if isinstance(obj, Project) else obj.project
        return project.investor.user_id == request.user.id


class DocumentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    الفصل السادس — رفع وثيقة واحدة. rejected سابقاً؟ الرفع الجديد
    يستبدل القديمة تلقائياً بفضل unique_together على (project, requirement).
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if project.investor.user_id != self.request.user.id:
            raise permissions.PermissionDenied("هذا المشروع ليس ملكك.")
        # إعادة رفع بعد رفض: حدّث السجل الموجود بدل خطأ تكرار
        Document.objects.filter(
            project=project, requirement=serializer.validated_data["requirement"]
        ).delete()
        serializer.save(status=Document.Status.PENDING)


class ApplicationViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplicationStatusSerializer

    @action(detail=False, methods=["post"], url_path="projects/(?P<project_id>[^/.]+)/submit", url_name="submit")
    def submit(self, request, project_id=None):
        """POST /api/workflow/projects/<project_id>/submit/ — الفصل السابع."""
        project = get_object_or_404(Project, pk=project_id)
        if project.investor.user_id != request.user.id:
            return Response({"detail": "هذا المشروع ليس ملكك."}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = submit_application(project)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(application).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="projects/(?P<project_id>[^/.]+)/status", url_name="status")
    def status_view(self, request, project_id=None):
        """
        GET /api/workflow/projects/<project_id>/status/
        الفصل السابع فصاعداً — لوحة المتابعة والخط الزمني الكامل.
        """
        application = get_object_or_404(Application, project_id=project_id)
        if application.project.investor.user_id != self.request.user.id:
            raise permissions.PermissionDenied("هذا الطلب ليس ملكك.")
        return Response(self.get_serializer(application).data)


