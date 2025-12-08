from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import generics, permissions, viewsets, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import (
    UserSerializer,
    UserMeUpdateSerializer,
    UserOnboardingRequestSerializer,
    UserOnboardingDecisionSerializer,
)
from .models import UserOnboardingRequest
from .permissions import IsSuperAdmin

import secrets
import string


User = get_user_model()


# =========================
# AUTH / TOKEN SERIALIZER
# =========================

class JalsetuTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # First login detection (before increment)
        must_change = getattr(user, "login_count", 0) == 0

        # Increment login_count for successful login
        if hasattr(user, "login_count"):
            user.login_count += 1
            user.save(update_fields=["login_count"])

        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "login_count": getattr(user, "login_count", None),
        }
        data["must_change_password"] = must_change
        return data


class JalsetuTokenObtainPairView(TokenObtainPairView):
    serializer_class = JalsetuTokenObtainPairSerializer


# =========================
# /me ENDPOINT
# =========================

class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UserMeUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


# =========================
# CHANGE PASSWORD (FIRST LOGIN, ETC.)
# =========================

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Body: { "old_password": "...", "new_password": "..." }
    Used especially when must_change_password == true on first login.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


# =========================
# ONBOARDING REQUEST VIEWSET
# =========================

class UserOnboardingRequestViewSet(viewsets.ModelViewSet):
    """
    - POST /api/auth/onboarding-requests/             (create request)
    - GET  /api/auth/onboarding-requests/             (list - SUPER_ADMIN)
    - GET  /api/auth/onboarding-requests/{id}/        (detail - SUPER_ADMIN)
    - POST /api/auth/onboarding-requests/{id}/decide/ (approve/reject with remark)
    """

    queryset = UserOnboardingRequest.objects.all().order_by("-created_at")
    serializer_class = UserOnboardingRequestSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            # Any logged-in user can raise an appointment request
            return [permissions.IsAuthenticated()]
        elif self.action in ["list", "retrieve", "decide"]:
            # Only Agency Admin / SUPER_ADMIN should see & decide
            return [IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()

    def _create_user_from_request(self, onboarding_request: UserOnboardingRequest):
        """
        Creates a User from onboarding request:
        - If user with same email already exists, reuse it
        - Otherwise, create new user with:
          - username from email prefix
          - secure random password
          - role & department from request
        - Sends email with temporary password (console backend for dev)
        """
        email = onboarding_request.email
        username = email.split("@")[0]

        # If user already exists → reuse it
        if User.objects.filter(email=email).exists():
            return User.objects.get(email=email)

        full_name = (onboarding_request.full_name or "").strip()
        first_name = ""
        last_name = ""
        if full_name:
            parts = full_name.split()
            if len(parts) == 1:
                first_name = parts[0]
            else:
                first_name = parts[0]
                # "Abhishek Malhotra Singh" -> "Malhotra Singh"
                last_name = " ".join(parts[1:])
        # Secure random password (12 chars)
        raw_password = "".join(
            secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
            for _ in range(12)
        )

        created_user = User.objects.create_user(
            username=username,
            email=email,
            password=raw_password,
            role=onboarding_request.requested_role,
            department=onboarding_request.department,
            is_active=True,
            first_name=first_name,
            last_name=last_name,
        )

        # Email credentials (console email backend in dev; will print in terminal)
        subject = "Your Jalsetu Account Credentials"
        message = (
            f"Dear {onboarding_request.full_name},\n\n"
            f"Your Jalsetu account has been approved.\n\n"
            f"Username: {username}\n"
            f"Temporary password: {raw_password}\n\n"
            f"For security reasons, you MUST log in and change your password at first login.\n\n"
            f"– Jalsetu System"
        )

        try:
            send_mail(
                subject,
                message,
                getattr(settings, "DEFAULT_FROM_EMAIL", "jalsetu-noreply@jalsetu.local"),
                [email],
                fail_silently=True,  # dev/demo: don't crash if email not configured
            )
        except Exception:
            # Ignore email failure in dev mode
            pass

        return created_user

    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        """
        SUPER_ADMIN decides:
        - { "action": "APPROVE" | "REJECT", "remark": "..." }
        """
        onboarding_request = self.get_object()
        decision_serializer = UserOnboardingDecisionSerializer(
            data=request.data,
            context={"onboarding_request": onboarding_request},
        )
        decision_serializer.is_valid(raise_exception=True)

        action_value = decision_serializer.validated_data["action"]
        remark = decision_serializer.validated_data.get("remark", "")

        onboarding_request.decision_remark = remark
        onboarding_request.decided_at = timezone.now()
        onboarding_request.decided_by = request.user

        if action_value == "APPROVE":
            created_user = self._create_user_from_request(onboarding_request)
            onboarding_request.status = UserOnboardingRequest.Status.APPROVED
            onboarding_request.created_user = created_user
        else:
            onboarding_request.status = UserOnboardingRequest.Status.REJECTED

        onboarding_request.save()

        return Response(
            UserOnboardingRequestSerializer(onboarding_request).data,
            status=status.HTTP_200_OK,
        )
