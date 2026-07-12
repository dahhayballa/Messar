from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InspectionViewSet, PaymentViewSet, LicenseViewSet

router = DefaultRouter()
router.register(r"inspections", InspectionViewSet, basename="inspection")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"", LicenseViewSet, basename="license")

urlpatterns = [
    path("", include(router.urls)),
]

