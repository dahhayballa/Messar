from django.urls import path
from .views import DocumentUploadView, SubmitApplicationView, ApplicationStatusView

urlpatterns = [
    path("documents/", DocumentUploadView.as_view(), name="document-upload"),
    path("projects/<int:project_id>/submit/", SubmitApplicationView.as_view(), name="application-submit"),
    path("projects/<int:project_id>/status/", ApplicationStatusView.as_view(), name="application-status"),
]
