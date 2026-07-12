from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.models import Project
from .models import Application, Document
from .serializers import ApplicationStatusSerializer, DocumentSerializer
from .services import submit_application


class IsProjectOwner(permissions.BasePermission):
    """المستثمر يرى ويعدّل وثائق/طلبات مشاريعه هو فقط."""

    def has_object_permission(self, request, view, obj):
        project = obj if isinstance(obj, Project) else obj.project
        return project.investor.user_id == request.user.id


class DocumentUploadView(generics.CreateAPIView):
    """
    POST /api/workflow/documents/
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


class SubmitApplicationView(APIView):
    """POST /api/workflow/projects/<project_id>/submit/ — الفصل السابع."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id):
        project = generics.get_object_or_404(Project, pk=project_id)
        if project.investor.user_id != request.user.id:
            return Response({"detail": "هذا المشروع ليس ملكك."}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = submit_application(project)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ApplicationStatusSerializer(application).data, status=status.HTTP_200_OK)


class ApplicationStatusView(generics.RetrieveAPIView):
    """
    GET /api/workflow/projects/<project_id>/status/
    الفصل السابع فصاعداً — لوحة المتابعة والخط الزمني الكامل.
    """
    serializer_class = ApplicationStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "project_id"

    def get_object(self):
        application = generics.get_object_or_404(Application, project_id=self.kwargs["project_id"])
        if application.project.investor.user_id != self.request.user.id:
            raise permissions.PermissionDenied("هذا الطلب ليس ملكك.")
        return application
