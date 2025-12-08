from rest_framework.permissions import BasePermission


def _has_role(user, *roles):
    return bool(
        user
        and user.is_authenticated
        and user.role in roles
        and not (user.role == "GUEST" and getattr(user, "is_guest_expired", lambda: False)())
    )


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, "SUPER_ADMIN")


class IsSeniorAnalystOrHigher(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, "SUPER_ADMIN", "SENIOR_ANALYST")


class IsAnalystOrHigher(BasePermission):
    def has_permission(self, request, view):
        return _has_role(
            request.user,
            "SUPER_ADMIN",
            "SENIOR_ANALYST",
            "JUNIOR_ANALYST",
        )


class IsGuest(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, "GUEST")


class IsITAdmin(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, "IT_ADMIN")


class IsAuditAuthority(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, "AUDIT")
