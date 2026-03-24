"""Tests for document permission SQL and Qdrant filters."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "shared", "python"))

from app.rbac.filters import get_allowed_scopes, build_qdrant_filter
from app.models.membership import ProjectMembership


def _make_membership(role: str, trade: str | None = None) -> ProjectMembership:
    m = ProjectMembership.__new__(ProjectMembership)
    m.id = "test"
    m.user_id = "u1"
    m.project_id = "p1"
    m.role = role
    m.assigned_trade = trade
    return m


class TestAllowedScopes:
    def test_admin_all_scopes(self):
        m = _make_membership("admin")
        scopes = get_allowed_scopes(m)
        assert len(scopes) == 5

    def test_subcontractor_limited(self):
        m = _make_membership("subcontractor", "electrical")
        scopes = get_allowed_scopes(m)
        assert "field_team" in scopes
        assert "trade_scoped" in scopes
        assert "management_only" not in scopes
        assert "project_full" not in scopes

    def test_owner_viewer_only_shared(self):
        m = _make_membership("owner_viewer")
        scopes = get_allowed_scopes(m)
        assert scopes == ["owner_shared"]


class TestQdrantFilter:
    def test_admin_filter(self):
        m = _make_membership("admin")
        f = build_qdrant_filter(m, "p1")
        assert f["must"][0]["key"] == "project_id"
        assert f["must"][0]["match"]["value"] == "p1"
        # Admin should have all scopes
        assert len(f["must"][1]["match"]["any"]) == 5

    def test_subcontractor_filter_includes_trade(self):
        m = _make_membership("subcontractor", "electrical")
        f = build_qdrant_filter(m, "p1")
        # Should have project_id, visibility_scope, and trade_scope filters
        assert len(f["must"]) == 3
        trade_filter = f["must"][2]
        assert trade_filter["key"] == "trade_scope"
        assert "electrical" in trade_filter["match"]["any"]

    def test_owner_viewer_filter(self):
        m = _make_membership("owner_viewer")
        f = build_qdrant_filter(m, "p1")
        scopes = f["must"][1]["match"]["any"]
        assert scopes == ["owner_shared"]
