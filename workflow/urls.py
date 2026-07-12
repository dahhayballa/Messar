from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, ApplicationViewSet

router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"", ApplicationViewSet, basename="application")

urlpatterns = [
    path("", include(router.urls)),
]

