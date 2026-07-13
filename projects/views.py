from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.models import ServiceType
from .models import Investor, Project
from .serializers import (
    OnboardingSerializer, ProjectSerializer, CheckNameSerializer,
    ProjectLocationSerializer, NewProjectSerializer,
)
from .services import create_full_onboarding, create_project_for_existing_investor, is_name_available


class ProjectViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "check_name":
            return CheckNameSerializer
        if self.action == "new_project":
            return NewProjectSerializer
        if self.action == "location":
            return ProjectLocationSerializer
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
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="new-project",
            permission_classes=[permissions.IsAuthenticated])
    def new_project(self, request):
        """
        POST /api/projects/new-project/
        الفصل الأخير («مَسار يعرف أحمد») — مستثمر مسجَّل مسبقاً يفتح
        مشروعاً ثانياً بلا تسجيل جديد.
        """
        try:
            investor = Investor.objects.get(user=request.user)
        except Investor.DoesNotExist:
            return Response(
                {"detail": "لا يوجد ملف مستثمر لهذا الحساب — استخدم onboarding أولاً."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = create_project_for_existing_investor(
                investor=investor,
                project_name=serializer.validated_data["project_name"],
                service_type=serializer.validated_data["service_type"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="location",
            permission_classes=[permissions.IsAuthenticated])
    def location(self, request, pk=None):
        """
        PATCH /api/projects/<pk>/location/
        الفصل الخامس — تحديد الولاية والبلدية والعنوان والإحداثيات.
        """
        project = get_object_or_404(Project, pk=pk)
        if project.investor.user_id != request.user.id:
            raise permissions.PermissionDenied("هذا المشروع ليس ملكك.")

        serializer = self.get_serializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        """
        GET /api/projects/mine/
        الفصل الأخير («مَسار يعرف أحمد») — كل مشاريع المستثمر المسجَّل
        دخوله حالياً، بلا حاجة لتذكّر أي رقم مشروع يدوياً.
        """
        try:
            investor = Investor.objects.get(user=request.user)
        except Investor.DoesNotExist:
            return Response([])

        projects = Project.objects.filter(investor=investor).order_by("-created_at")
        return Response(ProjectSerializer(projects, many=True).data)