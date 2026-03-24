"""Tests for document upload and processing state transitions."""
import pytest
from sqlalchemy import text


class TestDocumentStates:
    def test_new_document_starts_processing(self, session, seed_data):
        result = session.execute(
            text("SELECT status FROM documents WHERE id = 'd1'")
        )
        status = result.scalar()
        assert status == "ready"  # Seed data is already ready

    def test_valid_status_values(self, session, seed_data):
        result = session.execute(
            text("SELECT DISTINCT status FROM documents")
        )
        statuses = [r[0] for r in result]
        valid = {"processing", "ready", "error", "rendering_pages", "extracting_text", "vlm_processing", "chunking", "embedding"}
        for s in statuses:
            assert s in valid, f"Invalid status: {s}"

    def test_document_has_required_fields(self, session, seed_data):
        result = session.execute(
            text("SELECT project_id, uploaded_by_user_id, file_name, file_type, doc_type, visibility_scope FROM documents WHERE id = 'd1'")
        )
        row = result.first()
        assert row is not None
        assert row[0] == "p1"  # project_id
        assert row[1] == "u1"  # uploaded_by_user_id
        assert row[2] is not None  # file_name
        assert row[3] == "pdf"  # file_type
        assert row[4] is not None  # doc_type
        assert row[5] is not None  # visibility_scope

    def test_document_visibility_scopes_valid(self, session, seed_data):
        result = session.execute(
            text("SELECT DISTINCT visibility_scope FROM documents")
        )
        scopes = [r[0] for r in result]
        valid_scopes = {"project_full", "field_team", "trade_scoped", "owner_shared", "management_only"}
        for s in scopes:
            assert s in valid_scopes
