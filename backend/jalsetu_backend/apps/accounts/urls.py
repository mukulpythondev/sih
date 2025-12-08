from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    JalsetuTokenObtainPairView,
    MeView,
    UserOnboardingRequestViewSet,
    ChangePasswordView,
)

app_name = "accounts"

router = DefaultRouter()
router.register(
    r"onboarding-requests",
    UserOnboardingRequestViewSet,
    basename="onboarding-request",
)

urlpatterns = [
    path("login/", JalsetuTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("", include(router.urls)),
]
