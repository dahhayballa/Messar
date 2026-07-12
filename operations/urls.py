from django.urls import path
from .views import (
    MyInspectionListView, InspectionReportView,
    PaymentUploadView, PaymentVerifyView,
    ProjectLicensesView, LicensePublicVerifyView,
)

urlpatterns = [
    path("inspections/mine/", MyInspectionListView.as_view(), name="my-inspections"),
    path("inspections/<int:pk>/report/", InspectionReportView.as_view(), name="inspection-report"),

    path("payments/", PaymentUploadView.as_view(), name="payment-upload"),
    path("payments/<int:pk>/verify/", PaymentVerifyView.as_view(), name="payment-verify"),

    path("projects/<int:project_id>/licenses/", ProjectLicensesView.as_view(), name="project-licenses"),
    path("verify/<str:license_number>/", LicensePublicVerifyView.as_view(), name="license-public-verify"),
]
