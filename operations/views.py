from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

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


class InspectionViewSet(viewsets.GenericViewSet):
    serializer_class = InspectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInspector]

    def get_queryset(self):
        return Inspection.objects.filter(inspector=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "report":
            return InspectionReportSerializer
        return InspectionSerializer

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """GET /api/operations/inspections/mine/ — مهام المفتش المُسندة له."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="report")
    def report(self, request, pk=None):
        """
        POST /api/operations/inspections/<id>/report/
        الفصل الثامن — المفتش يرسل النتيجة، فيتحرك الـWorkflow تلقائياً.
        """
        inspection = get_object_or_404(Inspection, pk=pk, inspector=request.user)
        serializer = self.get_serializer(data=request.data)
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



class PaymentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un investisseur ne peut voir que ses paiements, un admin peut tout voir
        if self.request.user.role == "ADMIN" or self.request.user.is_staff:
            return Payment.objects.all().order_by("-created_at")
        return Payment.objects.filter(project__investor__user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        """POST /api/operations/payments/ — الفصل التاسع: المستثمر يرفع المخالصة."""
        project = serializer.validated_data["project"]
        if project.investor.user_id != self.request.user.id:
            raise permissions.PermissionDenied("هذا المشروع ليس ملكك.")
        serializer.save(status="PENDING")

    @action(detail=True, methods=["post"], url_path="verify", permission_classes=[permissions.IsAuthenticated, IsAdmin])
    def verify(self, request, pk=None):
        """
        POST /api/operations/payments/<id>/verify/
        الإدارة فقط — تأكيد المخالصة يُصدر الترخيص الأولي تلقائياً (الفصل العاشر).
        """
        payment = get_object_or_404(Payment, pk=pk)
        application = verify_payment(payment)
        return Response(ApplicationStatusSerializer(application).data)


class LicenseViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LicenseSerializer

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

    @action(detail=False, methods=["get"], url_path="projects/(?P<project_id>[^/.]+)/licenses", permission_classes=[permissions.IsAuthenticated])
    def project_licenses(self, request, project_id=None):
        """GET /api/operations/projects/<project_id>/licenses/ — تراخيص مشروع (أولي/نهائي)."""
        queryset = License.objects.filter(project_id=project_id).order_by("-issued_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="verify/(?P<license_number>[^/.]+)")
    def public_verify(self, request, license_number=None):
        """
        GET /api/operations/verify/<license_number>/
        تحقق علني بلا مصادقة — أي سائح يتأكد أن الترخيص ساري (فكرة السعودية).
        """
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


