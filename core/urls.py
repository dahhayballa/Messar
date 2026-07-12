from django.urls import path
from .views import ServiceTypeListView, ServiceTypeDetailView

urlpatterns = [
    path("services/", ServiceTypeListView.as_view(), name="service-list"),
    path("services/<int:pk>/", ServiceTypeDetailView.as_view(), name="service-detail"),
]
