from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from projects.models import Project
from .models import Application, Document
from .serializers import ApplicationStatusSerializer, DocumentSerializer
from .services import submit_application


class IsProjectOwner(permissions.BasePermission):
    """L'investisseur ne peut voir/modifier que ses propres objets liés."""

    def has_object_permission(self, request, view, obj):
        project = obj if isinstance(obj, Project) else obj.project
        return project.investor.user_id == request.user.id


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer le téléversement des pièces justificatives.
    POST /api/workflow/documents/ - Téléverser ou remplacer un document.
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        return Document.objects.filter(project__investor__user=self.request.user)

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


class ApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour suivre et soumettre l'application de licence.
    GET /api/workflow/applications/<project_id>/ - Consulter l'état et l'historique (Chapitre 7).
    POST /api/workflow/applications/<project_id>/submit/ - Soumettre le dossier (Chapitre 7).
    """
    serializer_class = ApplicationStatusSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]
    lookup_field = "project_id"

    def get_queryset(self):
        return Application.objects.filter(project__investor__user=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, project_id=None):
        project = generics.get_object_or_404(Project, pk=project_id)
        if project.investor.user_id != request.user.id:
            return Response({"detail": "هذا المشروع ليس ملكك."}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = submit_application(project)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ApplicationStatusSerializer(application).data, status=status.HTTP_200_OK)
