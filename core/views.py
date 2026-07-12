from rest_framework import generics, permissions
from .models import ServiceType
from .serializers import ServiceTypeSerializer


class ServiceTypeListView(generics.ListAPIView):
    """
    GET /api/services/
    يُستخدم في «الفصل الثاني: المعرفة قبل الالتزام» — يعرض الوثائق
    والمراحل قبل أي تسجيل، لذا الوصول مفتوح للجميع بلا مصادقة.
    """
    queryset = ServiceType.objects.prefetch_related("requirements").all()
    serializer_class = ServiceTypeSerializer
    permission_classes = [permissions.AllowAny]


class ServiceTypeDetailView(generics.RetrieveAPIView):
    """GET /api/services/<id>/ — تفاصيل نشاط واحد ووثائقه فقط."""
    queryset = ServiceType.objects.prefetch_related("requirements").all()
    serializer_class = ServiceTypeSerializer
    permission_classes = [permissions.AllowAny]
