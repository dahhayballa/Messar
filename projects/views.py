from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import ServiceType
from .serializers import OnboardingSerializer, ProjectSerializer, CheckNameSerializer
from .services import create_full_onboarding, is_name_available


class ProjectViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "check_name":
            return CheckNameSerializer
        return OnboardingSerializer

    @action(detail=False, methods=["get", "post"], url_path="check-name")
    def check_name(self, request):
        """
        GET/POST /api/projects/check-name/
        الفصل الثالث في الرحلة — بلا مصادقة، أي زائر يستطيع البحث.
        """
        data = request.data if request.method == "POST" else request.query_params
        serializer = CheckNameSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data["name"]
        service_type = serializer.validated_data["service_type"]

        available = is_name_available(name, service_type)
        return Response({"name": name, "service_type": service_type.name, "available": available})

    @action(detail=False, methods=["post"], url_path="onboarding")
    def onboarding(self, request):
        """
        POST /api/projects/onboarding/
        الفصل الرابع — شاشة واحدة تُنشئ الحساب والمستثمر وتحجز الاسم
        وتُنشئ المشروع، في عملية ذرّية واحدة (قاعدة 5.3).
        """
        serializer = self.get_serializer(data=request.data)
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


