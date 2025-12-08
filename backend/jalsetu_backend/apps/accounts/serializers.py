from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import UserOnboardingRequest

User = get_user_model()


# =========================
# USER SERIALIZERS
# =========================

class UserSerializer(serializers.ModelSerializer):
    """
    Used for GET /me (read-only)
    """
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "department",
            "access_expires_at",
            "login_count",   # added so we can debug
        ]
        read_only_fields = [
            "id",
            "role",
            "login_count",
            "username",
            "email",
        ]


class UserMeUpdateSerializer(serializers.ModelSerializer):
    """
    Used for PATCH /me
    """
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "department",
        ]


# =========================
# ONBOARDING SERIALIZERS
# =========================

class UserOnboardingRequestSerializer(serializers.ModelSerializer):
    """
    Normal representation of onboarding request object
    """
    class Meta:
        model = UserOnboardingRequest
        fields = [
            "id",
            "email",
            "full_name",
            "requested_role",
            "department",
            "status",
            "created_at",
            "decided_at",
            "decided_by",
            "decision_remark",
            "created_user",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "decided_at",
            "decided_by",
            "decision_remark",
            "created_user",
        ]


class UserOnboardingDecisionSerializer(serializers.Serializer):
    """
    For POST /onboarding-requests/{id}/decide/
    """
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    remark = serializers.CharField(allow_blank=True, required=False)

    def validate(self, attrs):
        request_obj: UserOnboardingRequest = self.context["onboarding_request"]

        if request_obj.status != UserOnboardingRequest.Status.PENDING:
            raise serializers.ValidationError("This request is already processed.")

        return attrs


# =========================
# CHANGE PASSWORD SERIALIZER
# =========================

class ChangePasswordSerializer(serializers.Serializer):
    """
    Used in POST /api/auth/change-password/
    Also used during first login
    """
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
