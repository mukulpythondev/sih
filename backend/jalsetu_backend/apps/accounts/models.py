from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):
    class Roles(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        SENIOR_ANALYST = "SENIOR_ANALYST", "Senior Analyst"
        JUNIOR_ANALYST = "JUNIOR_ANALYST", "Junior Analyst"
        GUEST = "GUEST", "Guest Reviewer"
        IT_ADMIN = "IT_ADMIN", "IT Admin / Integrator"
        AUDIT = "AUDIT", "Audit Authority"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=32,
        choices=Roles.choices,
        default=Roles.JUNIOR_ANALYST,
    )

    department = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Department / agency name (e.g., NTRO, NIA, Internal Cell)",
    )

    access_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="For guest or time-bound accounts.",
    )

    # 👇 NEW
    login_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of successful logins. Used to enforce first-time password change.",
    )

    def is_guest_expired(self) -> bool:
        if self.role != self.Roles.GUEST:
            return False
        if self.access_expires_at is None:
            return False
        return timezone.now() > self.access_expires_at

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserOnboardingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    requested_role = models.CharField(
        max_length=32,
        choices=User.Roles.choices,
        help_text="Role requested for this appointment.",
    )
    department = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    decided_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this request was approved/rejected.",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="onboarding_decisions",
        help_text="Agency admin who took the decision.",
    )
    decision_remark = models.TextField(
        blank=True,
        null=True,
        help_text="Reason/remark for approval or rejection.",
    )

    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="onboarding_requests",
        help_text="User account created from this request, if any.",
    )

    def __str__(self):
        return f"{self.email} ({self.requested_role}) [{self.status}]"
