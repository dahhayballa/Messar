from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import ServiceType
from .models import Project, Investor
from .serializers import OnboardingSerializer, ProjectSerializer, ProjectCreateSerializer
from .services import create_full_onboarding, is_name_available, create_project_for_existing_investor


class IsProjectOwner(permissions.BasePermission):
    """L'investisseur ne peut voir/modifier que ses propres projets."""

    def has_object_permission(self, request, view, obj):
        return obj.investor.user_id == request.user.id


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def get_queryset(self):
        # Un utilisateur authentifié ne voit que ses propres projets
        if self.request.user.is_authenticated:
            return Project.objects.filter(investor__user=self.request.user).order_by("-created_at")
        return Project.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        elif self.action == "onboarding":
            return OnboardingSerializer
        return ProjectSerializer

    def create(self, request, *args, **kwargs):
        # Création d'un projet par un investisseur déjà existant et connecté (Chapitre Final)
        try:
            investor = request.user.investor
        except Investor.DoesNotExist:
            return Response(
                {"detail": "Ce compte n'est pas lié à un profil investisseur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            project = create_project_for_existing_investor(
                investor=investor,
                project_name=data["project_name"],
                service_type=data["service_type"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny], url_path="check-name")
    def check_name(self, request):
        """
        GET /api/projects/check-name/?name=رحلات الصحراء&service_type=3
        Vérification de la disponibilité d'un nom (Chapitre 3).
        """
        name = request.query_params.get("name", "").strip()
        service_type_id = request.query_params.get("service_type")

        if not name or not service_type_id:
            return Response(
                {"detail": "Les champs name et service_type sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service_type = ServiceType.objects.get(pk=service_type_id)
        except ServiceType.DoesNotExist:
            return Response({"detail": "Le type d'activité n'existe pas."}, status=status.HTTP_404_NOT_FOUND)

        available = is_name_available(name, service_type)
        return Response({"name": name, "service_type": service_type.name, "available": available})

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny], url_path="onboarding")
    def onboarding(self, request):
        """
        POST /api/projects/onboarding/
        Création de compte + profil investisseur + projet + réservation de nom (Chapitre 4).
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            project = create_full_onboarding(
                email=data["email"], phone=data["phone"], password=data["password"],
                investor_type=data["investor_type"], full_name=data["full_name"],
                nationality=data["nationality"], national_id=data["national_id"],
                project_name=data["project_name"], service_type=data["service_type"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
