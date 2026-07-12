from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceTypeViewSet

router = DefaultRouter()
router.register("services", ServiceTypeViewSet, basename="service")

urlpatterns = [
    path("", include(router.urls)),
]

