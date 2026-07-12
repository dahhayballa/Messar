from django.urls import path
from .views import CheckNameView, OnboardingView

urlpatterns = [
    path("check-name/", CheckNameView.as_view(), name="check-name"),
    path("onboarding/", OnboardingView.as_view(), name="onboarding"),
]
