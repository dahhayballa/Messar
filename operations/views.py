from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Inspection, Payment, License
from .serializers import (
    InspectionSerializer, InspectionReportSerializer,
    PaymentSerializer, LicenseSerializer,
)
from .services import submit_inspection_report, verify_payment
from workflow.serializers import ApplicationStatusSerializer


class IsInspector(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "INSPECTOR"


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "ADMIN" or request.user.is_staff


class InspectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les inspections.
    GET /api/operations/inspections/ - Liste des inspections de l'inspecteur connecté (Chapitre 8).
    POST /api/operations/inspections/<id>/report/ - Soumettre le rapport d'inspection terrain (Chapitre 8).
    """
    serializer_class = InspectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInspector]

    def get_queryset(self):
        return Inspection.objects.filter(inspector=self.request.user).order_by("-created_at")

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser], url_path="report")
    def report(self, request, pk=None):
        inspection = generics.get_object_or_404(Inspection, pk=pk, inspector=request.user)
        serializer = InspectionReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        application = submit_inspection_report(
            inspection,
            result=data["result"],
            notes=data.get("notes", ""),
            latitude=data["latitude"],
            longitude=data["longitude"],
            checklist_completed=data["checklist_completed"],
            photo=data.get("photo"),
        )
        return Response(ApplicationStatusSerializer(application).data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les paiements.
    POST /api/operations/payments/ - Uploader le reçu de paiement (Chapitre 9).
    POST /api/operations/payments/<id>/verify/ - Confirmer le paiement (Admin) (Chapitre 9).
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un investisseur ne peut voir que ses paiements, un admin peut tout voir
        if self.request.user.role == "ADMIN" or self.request.user.is_staff:
            return Payment.objects.all().order_by("-created_at")
        return Payment.objects.filter(project__investor__user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if project.investor.user_id != self.request.user.id:
            raise permissions.PermissionDenied("هذا المشروع ليس ملكك.")
        serializer.save(status="PENDING")

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAdmin])
    def verify(self, request, pk=None):
        payment = generics.get_object_or_404(Payment, pk=pk)
        application = verify_payment(payment)
        return Response(ApplicationStatusSerializer(application).data)


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour gérer et vérifier les licences.
    GET /api/operations/licenses/?project_id=<id> - Consulter les licences d'un projet (Chapitre 10 & 11).
    GET /api/operations/licenses/verify/<license_number>/ - Vérification publique de licence (Chapitre 11).
    """
    serializer_class = LicenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get("project_id")
        if not project_id:
            # Si aucun ID de projet n'est passé, les admins/inspecteurs peuvent voir toutes les licences.
            if self.request.user.role in ["ADMIN", "INSPECTOR"] or self.request.user.is_staff:
                return License.objects.all().order_by("-issued_at")
            return License.objects.filter(project__investor__user=self.request.user).order_by("-issued_at")
        
        queryset = License.objects.filter(project_id=project_id)
        if self.request.user.role == "INVESTOR":
            queryset = queryset.filter(project__investor__user=self.request.user)
        return queryset.order_by("-issued_at")

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny], url_path="verify/(?P<license_number>[^/.]+)")
    def verify_public(self, request, license_number=None):
        try:
            license_obj = License.objects.select_related("project").get(license_number=license_number)
        except License.DoesNotExist:
            return Response({"valid": False, "detail": "رقم الترخيص غير موجود."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "valid": True,
            "license_number": license_obj.license_number,
            "type": license_obj.get_type_display(),
            "project_name": license_obj.project.name,
            "service_type": license_obj.project.service_type.name,
            "issued_at": license_obj.issued_at,
            "expires_at": license_obj.expires_at,
        })
