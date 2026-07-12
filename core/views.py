from rest_framework import viewsets, permissions
from .models import ServiceType
from .serializers import ServiceTypeSerializer


class ServiceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    يُستخدم في «الفصل الثاني: المعرفة قبل الالتزام» — يعرض الوثائق
    والمراحل قبل أي تسجيل، لذا الوصول مفتوح للجميع بلا مصادقة.
    """
    queryset = ServiceType.objects.prefetch_related("requirements").all()
    serializer_class = ServiceTypeSerializer
    permission_classes = [permissions.AllowAny]
