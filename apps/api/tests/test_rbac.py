"""Tests for RBAC permission filtering."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared", "python"))

from shared.roles import ProjectRole, VisibilityScope, ROLE_VISIBILITY_MAP, ROLE_PERMISSIONS


class TestRoleVisibilityMap:
    def test_admin_sees_all_scopes(self):
        scopes = ROLE_VISIBILITY_MAP[ProjectRole.ADMIN]
        assert len(scopes) == 5
        assert VisibilityScope.MANAGEMENT_ONLY in scopes

    def test_pm_sees_all_scopes(self):
        scopes = ROLE_VISIBILITY_MAP[ProjectRole.PROJECT_MANAGER]
        assert len(scopes) == 5

    def test_superintendent_no_management_only(self):
        scopes = ROLE_VISIBILITY_MAP[ProjectRole.SUPERINTENDENT]
        assert VisibilityScope.MANAGEMENT_ONLY not in scopes
        assert VisibilityScope.PROJECT_FULL in scopes
        assert VisibilityScope.FIELD_TEAM in scopes

    def test_subcontractor_limited_scopes(self):
        scopes = ROLE_VISIBILITY_MAP[ProjectRole.SUBCONTRACTOR]
        assert scopes == {VisibilityScope.FIELD_TEAM, VisibilityScope.TRADE_SCOPED}
        assert VisibilityScope.PROJECT_FULL not in scopes
        assert VisibilityScope.MANAGEMENT_ONLY not in scopes
        assert VisibilityScope.OWNER_SHARED not in scopes

    def test_owner_viewer_only_owner_shared(self):
        scopes = ROLE_VISIBILITY_MAP[ProjectRole.OWNER_VIEWER]
        assert scopes == {VisibilityScope.OWNER_SHARED}


class TestRolePermissions:
    def test_admin_full_permissions(self):
        perms = ROLE_PERMISSIONS[ProjectRole.ADMIN]
        assert "project.create" in perms
        assert "member.manage" in perms
        assert "audit.view" in perms
        assert "document.upload" in perms

    def test_owner_viewer_read_only(self):
        perms = ROLE_PERMISSIONS[ProjectRole.OWNER_VIEWER]
        assert "document.view" in perms
        assert "chat.query" in perms
        assert "document.upload" not in perms
        assert "member.manage" not in perms
        assert "audit.view" not in perms

    def test_subcontractor_limited_upload(self):
        perms = ROLE_PERMISSIONS[ProjectRole.SUBCONTRACTOR]
        assert "document.upload" in perms
        assert "document.view" in perms
        assert "member.manage" not in perms

    def test_superintendent_no_member_manage(self):
        perms = ROLE_PERMISSIONS[ProjectRole.SUPERINTENDENT]
        assert "document.upload" in perms
        assert "chat.query" in perms
        assert "member.manage" not in perms
