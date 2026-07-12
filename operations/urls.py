from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InspectionViewSet, PaymentViewSet, LicenseViewSet

router = DefaultRouter()
router.register("inspections", InspectionViewSet, basename="inspection")
router.register("payments", PaymentViewSet, basename="payment")
router.register("licenses", LicenseViewSet, basename="license")

urlpatterns = [
    path("", include(router.urls)),
]

