from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

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


class MyInspectionListView(generics.ListAPIView):
    """GET /api/operations/inspections/mine/ — مهام المفتش المُسندة له."""
    serializer_class = InspectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInspector]

    def get_queryset(self):
        return Inspection.objects.filter(inspector=self.request.user).order_by("-created_at")


class InspectionReportView(APIView):
    """
    POST /api/operations/inspections/<id>/report/
    الفصل الثامن — المفتش يرسل النتيجة، فيتحرك الـWorkflow تلقائياً.
    """
    permission_classes = [permissions.IsAuthenticated, IsInspector]

    def post(self, request, pk):
        inspection = generics.get_object_or_404(Inspection, pk=pk, inspector=request.user)
        serializer = InspectionReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = submit_inspection_report(
            inspection, result=serializer.validated_data["result"],
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(ApplicationStatusSerializer(application).data)


class PaymentUploadView(generics.CreateAPIView):
    """POST /api/operations/payments/ — الفصل التاسع: المستثمر يرفع المخالصة."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if project.investor.user_id != self.request.user.id:
            raise permissions.PermissionDenied("هذا المشروع ليس ملكك.")
        serializer.save(status="PENDING")


class PaymentVerifyView(APIView):
    """
    POST /api/operations/payments/<id>/verify/
    الإدارة فقط — تأكيد المخالصة يُصدر الترخيص الأولي تلقائياً (الفصل العاشر).
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        payment = generics.get_object_or_404(Payment, pk=pk)
        application = verify_payment(payment)
        return Response(ApplicationStatusSerializer(application).data)


class ProjectLicensesView(generics.ListAPIView):
    """GET /api/operations/projects/<project_id>/licenses/ — تراخيص مشروع (أولي/نهائي)."""
    serializer_class = LicenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return License.objects.filter(project_id=self.kwargs["project_id"]).order_by("-issued_at")


class LicensePublicVerifyView(APIView):
    """
    GET /api/operations/verify/<license_number>/
    تحقق علني بلا مصادقة — أي سائح يتأكد أن الترخيص ساري (فكرة السعودية).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, license_number):
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
