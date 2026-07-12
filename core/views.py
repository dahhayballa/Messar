from rest_framework import viewsets, permissions
from .models import ServiceType
from .serializers import ServiceTypeSerializer


class ServiceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les types d'activités (ServiceType) et leurs pièces requises.
    GET /api/services/
    GET /api/services/<id>/
    Accès ouvert à tous sans authentification (Chapitre 1 et 2).
    """
    queryset = ServiceType.objects.prefetch_related("requirements").all()
    serializer_class = ServiceTypeSerializer
    permission_classes = [permissions.AllowAny]

