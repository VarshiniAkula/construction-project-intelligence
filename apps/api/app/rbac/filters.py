"""RBAC scope helpers."""
from app.shared_roles import ProjectRole, VisibilityScope, ROLE_VISIBILITY_MAP


def get_allowed_scopes(membership) -> list[str]:
    role = ProjectRole(membership.role)
    return [s.value for s in ROLE_VISIBILITY_MAP.get(role, set())]
