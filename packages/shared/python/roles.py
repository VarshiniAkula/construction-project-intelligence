"""Shared role definitions for BuildDocs AI."""
import enum


class ProjectRole(str, enum.Enum):
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    SUPERINTENDENT = "superintendent"
    SUBCONTRACTOR = "subcontractor"
    OWNER_VIEWER = "owner_viewer"


class VisibilityScope(str, enum.Enum):
    PROJECT_FULL = "project_full"
    FIELD_TEAM = "field_team"
    TRADE_SCOPED = "trade_scoped"
    OWNER_SHARED = "owner_shared"
    MANAGEMENT_ONLY = "management_only"


class DocType(str, enum.Enum):
    DRAWING = "drawing"
    SPECIFICATION = "specification"
    RFI = "rfi"
    SUBMITTAL = "submittal"
    DAILY_REPORT = "daily_report"
    MEETING_MINUTES = "meeting_minutes"
    SAFETY = "safety"
    CHANGE_ORDER = "change_order"
    GENERAL = "general"


class DocStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# Role -> allowed visibility scopes
ROLE_VISIBILITY_MAP: dict[ProjectRole, set[VisibilityScope]] = {
    ProjectRole.ADMIN: {
        VisibilityScope.PROJECT_FULL,
        VisibilityScope.FIELD_TEAM,
        VisibilityScope.TRADE_SCOPED,
        VisibilityScope.OWNER_SHARED,
        VisibilityScope.MANAGEMENT_ONLY,
    },
    ProjectRole.PROJECT_MANAGER: {
        VisibilityScope.PROJECT_FULL,
        VisibilityScope.FIELD_TEAM,
        VisibilityScope.TRADE_SCOPED,
        VisibilityScope.OWNER_SHARED,
        VisibilityScope.MANAGEMENT_ONLY,
    },
    ProjectRole.SUPERINTENDENT: {
        VisibilityScope.PROJECT_FULL,
        VisibilityScope.FIELD_TEAM,
        VisibilityScope.TRADE_SCOPED,
        VisibilityScope.OWNER_SHARED,
    },
    ProjectRole.SUBCONTRACTOR: {
        VisibilityScope.FIELD_TEAM,
        VisibilityScope.TRADE_SCOPED,
    },
    ProjectRole.OWNER_VIEWER: {
        VisibilityScope.OWNER_SHARED,
    },
}

# Role -> allowed actions
ROLE_PERMISSIONS: dict[ProjectRole, set[str]] = {
    ProjectRole.ADMIN: {
        "project.create", "project.edit", "project.view",
        "member.manage", "member.view",
        "document.upload", "document.view", "document.manage_visibility",
        "chat.query",
        "audit.view",
    },
    ProjectRole.PROJECT_MANAGER: {
        "project.edit", "project.view",
        "member.manage", "member.view",
        "document.upload", "document.view", "document.manage_visibility",
        "chat.query",
        "audit.view",
    },
    ProjectRole.SUPERINTENDENT: {
        "project.view",
        "member.view",
        "document.upload", "document.view",
        "chat.query",
    },
    ProjectRole.SUBCONTRACTOR: {
        "project.view",
        "document.upload", "document.view",
        "chat.query",
    },
    ProjectRole.OWNER_VIEWER: {
        "project.view",
        "document.view",
        "chat.query",
    },
}

# Allowed upload doc types per role
ROLE_UPLOAD_DOC_TYPES: dict[ProjectRole, set[DocType]] = {
    ProjectRole.ADMIN: set(DocType),
    ProjectRole.PROJECT_MANAGER: set(DocType),
    ProjectRole.SUPERINTENDENT: {
        DocType.DAILY_REPORT, DocType.SAFETY, DocType.GENERAL,
    },
    ProjectRole.SUBCONTRACTOR: {
        DocType.SUBMITTAL, DocType.RFI, DocType.GENERAL,
    },
    ProjectRole.OWNER_VIEWER: set(),
}
