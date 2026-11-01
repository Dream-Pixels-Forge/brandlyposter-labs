"""Tests for client approval tools."""
import shutil

import pytest


class TestClientApproval:
    """Test client approval workflow tools."""

    @pytest.fixture
    def test_project(self):
        """Create a test project with manifest."""
        from server import PROJECTS_DIR, ProjectManifest

        # Clean up any existing
        test_dir = PROJECTS_DIR / "test-approval"
        if test_dir.exists():
            shutil.rmtree(test_dir)

        project = ProjectManifest(
            project_id="test-approval",
            subject_id="test-subject",
            poster_id="test-poster",
            genre="thriller",
            master_prompt="Test prompt",
            qa_score="6/6",
            qa_passed=True,
        )
        project.save()

        yield "test-approval"

        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_share_review_returns_url(self, test_project):
        """Test brandly_share_review returns review URL."""
        from server import brandly_share_review

        result = brandly_share_review(test_project)

        assert "review_url" in result
        assert "project_id" in result
        assert "review_id" in result
        assert result["project_id"] == test_project
        assert "file://" in result["review_url"]

    def test_compare_versions_returns_structure(self):
        """Test brandly_compare_versions returns comparison structure."""
        from server import brandly_compare_versions

        result = brandly_compare_versions(
            variant_a_path="/path/to/variant_a.png",
            variant_b_path="/path/to/variant_b.png",
        )

        assert "variant_a" in result
        assert "variant_b" in result
        assert "comparison_path" in result
        assert result["variant_a"] == "/path/to/variant_a.png"

    def test_approve_version_locks_project(self, test_project):
        """Test brandly_approve_version locks project."""
        from server import ProjectManifest, brandly_approve_version

        result = brandly_approve_version(
            project_id=test_project,
            version_id="v1",
            client_signature="Client Approved",
        )

        assert result["locked"] is True
        assert result["final_version"] == "v1"
        assert result["project_id"] == test_project

        # Verify manifest updated
        project = ProjectManifest.load(test_project)
        assert project.approved is True
        assert project.approved_version == "v1"

    def test_share_review_missing_project_graceful(self):
        """Missing project must not crash share_review."""
        from server import brandly_share_review

        result = brandly_share_review("definitely-not-a-project")

        assert result["pass"] is False or "error" in result
        assert "project_id" in result

    def test_approve_version_missing_project_graceful(self):
        """Missing project must not crash approve_version."""
        from server import brandly_approve_version

        result = brandly_approve_version(
            project_id="definitely-not-a-project",
            version_id="v1",
            client_signature="x",
        )

        assert result["pass"] is False or "error" in result
        assert "project_id" in result