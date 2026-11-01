"""End-to-end integration test."""
import pytest
from pathlib import Path
import tempfile
import shutil


def _create_test_image(path: Path):
    """Create a simple test image."""
    from PIL import Image
    img = Image.new('RGB', (512, 512), color=(100, 100, 120))
    img.save(path)


class TestIntegration:
    """End-to-end integration test of the full workflow."""

    def test_full_workflow_subject_to_approval(self):
        """Test complete workflow: subject -> poster -> QA -> export -> approve."""
        from server import (
            brandly_subject_save,
            brandly_create_poster,
            brandly_qa_check,
            brandly_batch_export,
            brandly_approve_version,
            ProjectManifest,
            PROJECTS_DIR,
        )

        # Clean up
        test_dir = PROJECTS_DIR / "integration-test"
        if test_dir.exists():
            shutil.rmtree(test_dir)

        # 1. Save subject
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            ref_path = Path(f.name)
        _create_test_image(ref_path)

        try:
            subject_result = brandly_subject_save(
                subject_id="integration-subject",
                reference_image_path=str(ref_path),
                name="Integration Test Subject",
                story="A test visionary leader",
                outfit="test outfit",
            )
            assert subject_result["embedding_stored"] is True

            # 2. Create poster
            poster_result = brandly_create_poster(
                subject_id="integration-subject",
                genre="thriller",
                title="INTEGRATION TEST",
                subtitle="THE WORKFLOW",
                tagline="End to end works",
            )
            assert "master_prompt" in poster_result
            assert poster_result["subject_id"] == "integration-subject"

            # 3. Run QA (using the reference image as stand-in for generated)
            qa_result = brandly_qa_check(str(ref_path), subject_id="integration-subject")
            assert "score" in qa_result
            assert "checks" in qa_result
            assert len(qa_result["checks"]) == 6

            # 4. Create project manifest manually (in real flow, would be created after image gen)
            from server import ProjectManifest
            project = ProjectManifest(
                project_id="integration-test",
                subject_id="integration-subject",
                poster_id="integration-poster",
                genre="thriller",
                master_prompt=poster_result["master_prompt"],
                qa_score=qa_result["score"],
                qa_passed=qa_result["pass"],
            )
            project.save()

            # 5. Batch export
            export_result = brandly_batch_export(
                project_id="integration-test",
                formats=["theatrical", "deck", "social", "story"],
                generated_image_path=str(ref_path),
            )
            assert len(export_result["variants"]) == 4

            # 6. Approve
            approve_result = brandly_approve_version(
                project_id="integration-test",
                version_id="v1",
                client_signature="Integration Test Approved",
            )
            assert approve_result["locked"] is True

            # Verify final state
            final_project = ProjectManifest.load("integration-test")
            assert final_project.approved is True
            assert final_project.approved_version == "v1"
            assert len(final_project.variants) == 4

        finally:
            ref_path.unlink(missing_ok=True)
            if test_dir.exists():
                shutil.rmtree(test_dir)