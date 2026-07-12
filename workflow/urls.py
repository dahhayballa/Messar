from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, ApplicationViewSet

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("applications", ApplicationViewSet, basename="application")

urlpatterns = [
    path("", include(router.urls)),
]

