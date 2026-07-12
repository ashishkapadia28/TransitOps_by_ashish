from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        allowed_roles = getattr(view, "allowed_roles", self.allowed_roles)
        if not allowed_roles:
            return True

        return user.role in allowed_roles or user.is_superuser
