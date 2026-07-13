from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from projects.models import Project
from .models import Application, Document
from .serializers import ApplicationStatusSerializer, DocumentSerializer, DocumentReviewSerializer
from .services import approve_application_for_inspection, review_document, submit_application


class IsProjectOwner(permissions.BasePermission):
    """L'investisseur ne peut voir/modifier que ses propres objets liés."""

    def has_object_permission(self, request, view, obj):
        project = obj if isinstance(obj, Project) else obj.project
        return project.investor.user_id == request.user.id


class IsAdmin(permissions.BasePermission):
    """يسمح فقط للموظف الإداري (role=ADMIN) أو أي مستخدم is_staff."""

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "ADMIN" or request.user.is_staff


class DocumentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    الفصل السادس — رفع وثيقة واحدة. rejected سابقاً؟ الرفع الجديد
    يستبدل القديمة تلقائياً بفضل unique_together على (project, requirement).
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        return Document.objects.filter(project__investor__user=self.request.user)

    def get_permissions(self):
        if self.action == "review":
            return [permissions.IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if project.investor.user_id != self.request.user.id:
            raise permissions.PermissionDenied("هذا المشروع ليس ملكك.")

        # Supprimer le document existant du même type s'il y a un ré-upload après rejet (Chapitre 6 & 7)
        Document.objects.filter(
            project=project,
            requirement=serializer.validated_data["requirement"]
        ).delete()
        serializer.save(status=Document.Status.PENDING)

    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        """
        POST /api/workflow/documents/<pk>/review/
        الفصل السابع — الإداري فقط. يرفض/يقبل وثيقة واحدة بعينها.
        get_queryset مقيَّد بالمستثمر، لذا نستخدم Document.objects مباشرة هنا.
        """
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review_document(
            document,
            approved=serializer.validated_data["approved"],
            rejection_reason=serializer.validated_data.get("rejection_reason", ""),
        )
        return Response(DocumentSerializer(document).data)


class ApplicationViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplicationStatusSerializer

    def get_permissions(self):
        if self.action == "approve":
            return [permissions.IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

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

    @action(detail=False, methods=["post"], url_path="projects/(?P<project_id>[^/.]+)/approve", url_name="approve")
    def approve(self, request, project_id=None):
        """
        POST /api/workflow/projects/<project_id>/approve/
        الفصل السابع (نهايته) — الإداري فقط. موافقة كاملة على الملف،
        ينتقل الطلب لجدولة المعاينة الميدانية.
        """
        application = get_object_or_404(Application, project_id=project_id)
        application = approve_application_for_inspection(application)
        return Response(self.get_serializer(application).data)
