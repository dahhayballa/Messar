from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ServiceType
from .serializers import OnboardingSerializer, ProjectSerializer
from .services import create_full_onboarding, is_name_available


class CheckNameView(APIView):
    """
    GET /api/projects/check-name/?name=رحلات الصحراء&service_type=3
    الفصل الثالث في الرحلة — بلا مصادقة، أي زائر يستطيع البحث.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        name = request.query_params.get("name", "").strip()
        service_type_id = request.query_params.get("service_type")

        if not name or not service_type_id:
            return Response(
                {"detail": "الحقلان name وservice_type إلزاميان."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service_type = ServiceType.objects.get(pk=service_type_id)
        except ServiceType.DoesNotExist:
            return Response({"detail": "نوع النشاط غير موجود."}, status=status.HTTP_404_NOT_FOUND)

        available = is_name_available(name, service_type)
        return Response({"name": name, "service_type": service_type.name, "available": available})


class OnboardingView(APIView):
    """
    POST /api/projects/onboarding/
    الفصل الرابع — شاشة واحدة تُنشئ الحساب والمستثمر وتحجز الاسم
    وتُنشئ المشروع، في عملية ذرّية واحدة (قاعدة 5.3).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
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
            # مثال: الاسم لم يعد متاحاً (حجزه شخص آخر بين التحقق والإرسال)
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
