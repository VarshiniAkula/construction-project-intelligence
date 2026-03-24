"""Tests for chat retrieval filter verification."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared", "python"))

from app.rbac.filters import build_qdrant_filter
from app.models.membership import ProjectMembership


def _make_membership(role: str, trade: str | None = None) -> ProjectMembership:
    m = ProjectMembership.__new__(ProjectMembership)
    m.id = "test"
    m.user_id = "u1"
    m.project_id = "p1"
    m.role = role
    m.assigned_trade = trade
    return m


class TestChatRetrievalFilters:
    """Verify that Qdrant filters enforce access rules correctly."""

    def test_admin_sees_all_documents(self):
        m = _make_membership("admin")
        f = build_qdrant_filter(m, "p1")
        scopes = f["must"][1]["match"]["any"]
        assert "management_only" in scopes
        assert "owner_shared" in scopes
        assert "project_full" in scopes

    def test_subcontractor_cannot_see_management_docs(self):
        m = _make_membership("subcontractor", "electrical")
        f = build_qdrant_filter(m, "p1")
        scopes = f["must"][1]["match"]["any"]
        assert "management_only" not in scopes
        assert "project_full" not in scopes
        assert "owner_shared" not in scopes

    def test_subcontractor_filter_restricts_to_trade(self):
        m = _make_membership("subcontractor", "electrical")
        f = build_qdrant_filter(m, "p1")
        # Should include trade_scope filter
        trade_conditions = [c for c in f["must"] if c.get("key") == "trade_scope"]
        assert len(trade_conditions) == 1
        assert "electrical" in trade_conditions[0]["match"]["any"]

    def test_owner_viewer_only_sees_owner_shared(self):
        m = _make_membership("owner_viewer")
        f = build_qdrant_filter(m, "p1")
        scopes = f["must"][1]["match"]["any"]
        assert scopes == ["owner_shared"]

    def test_pm_sees_everything_in_project(self):
        m = _make_membership("project_manager")
        f = build_qdrant_filter(m, "p1")
        scopes = f["must"][1]["match"]["any"]
        assert len(scopes) == 5

    def test_superintendent_no_management_only(self):
        m = _make_membership("superintendent")
        f = build_qdrant_filter(m, "p1")
        scopes = f["must"][1]["match"]["any"]
        assert "management_only" not in scopes
        assert "project_full" in scopes
        assert "field_team" in scopes

    def test_filter_always_includes_project_id(self):
        """Every filter must scope to the correct project."""
        for role in ["admin", "project_manager", "superintendent", "subcontractor", "owner_viewer"]:
            m = _make_membership(role, "electrical" if role == "subcontractor" else None)
            f = build_qdrant_filter(m, "p1")
            project_filter = f["must"][0]
            assert project_filter["key"] == "project_id"
            assert project_filter["match"]["value"] == "p1"

    def test_different_projects_different_filters(self):
        m = _make_membership("admin")
        f1 = build_qdrant_filter(m, "project-a")
        f2 = build_qdrant_filter(m, "project-b")
        assert f1["must"][0]["match"]["value"] == "project-a"
        assert f2["must"][0]["match"]["value"] == "project-b"
