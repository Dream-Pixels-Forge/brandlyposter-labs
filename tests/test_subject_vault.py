"""Tests for subject vault: save, match, earring baseline."""
import pytest
from pathlib import Path
import tempfile
import shutil

# Skip if no test image available
def _create_test_image(path: Path, color=(128, 128, 128), size=(512, 512)):
    """Create a simple test image."""
    from PIL import Image
    img = Image.new('RGB', size, color=color)
    img.save(path)
    return path


class TestSubjectVault:
    """Test subject vault operations."""

    @pytest.fixture
    def test_image(self):
        """Create a temporary test image."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            path = Path(f.name)
        _create_test_image(path)
        yield str(path)
        if path.exists():
            path.unlink()

    def test_subject_save_creates_profile(self, test_image):
        """Test subject save creates profile with embedding."""
        from server import brandly_subject_save, SubjectProfile, SUBJECTS_DIR

        result = brandly_subject_save(
            subject_id="test-subject-save",
            reference_image_path=test_image,
            name="Test Subject",
            story="A test story",
            outfit="Test outfit",
        )

        assert result["subject_id"] == "test-subject-save"
        assert result["embedding_stored"] is True
        assert "earring_baseline" in result

        # Verify file exists
        profile_path = SUBJECTS_DIR / "test-subject-save" / "profile.json"
        assert profile_path.exists()

        # Load and verify
        subject = SubjectProfile.load("test-subject-save")
        assert subject.name == "Test Subject"
        assert subject.story == "A test story"
        assert subject.outfit == "Test outfit"
        assert subject.face_embedding is not None
        assert len(subject.face_embedding) == 512  # CLIP base patch32 = 512 dims

    def test_subject_match_returns_similarity(self, test_image):
        """Test subject match returns similarity score."""
        from server import brandly_subject_save, brandly_subject_match

        # Save subject
        brandly_subject_save(
            subject_id="test-match",
            reference_image_path=test_image,
            name="Match Test",
        )

        # Match against same image (should be high similarity)
        result = brandly_subject_match(
            generated_image_path=test_image,
            subject_id="test-match",
        )

        assert result["subject_id"] == "test-match"
        assert "similarity" in result
        assert 0.0 <= result["similarity"] <= 1.0
        assert "pass" in result
        assert "threshold" in result

    def test_subject_match_below_threshold(self, test_image):
        """Test subject match fails below threshold."""
        from server import brandly_subject_save, brandly_subject_match, SubjectProfile

        # Save subject with high threshold
        brandly_subject_save(
            subject_id="test-high-threshold",
            reference_image_path=test_image,
            name="High Threshold",
        )

        # Manually set threshold > 1.0 (impossible to pass since max similarity is 1.0)
        subject = SubjectProfile.load("test-high-threshold")
        subject.likeness_threshold = 1.0001  # Impossible to pass
        subject.save()

        # Match should fail
        result = brandly_subject_match(
            generated_image_path=test_image,
            subject_id="test-high-threshold",
        )

        assert result["pass"] is False
        assert result["similarity"] <= 1.0

    def test_earring_check_returns_structure(self, test_image):
        """Test earring check returns expected structure."""
        from server import brandly_earring_check

        result = brandly_earring_check(test_image)

        # Even if no earrings detected, structure should be correct
        assert "pass" in result
        if not result["pass"]:
            assert "reason" in result or "candidates" in result

    def test_subject_match_missing_subject_graceful(self):
        """Missing subject must not crash; returns graceful pass=False result."""
        from server import brandly_subject_match

        result = brandly_subject_match(
            generated_image_path="/tmp/does-not-exist.png",
            subject_id="definitely-not-a-subject",
        )

        assert result["pass"] is False
        assert "reason" in result
        assert "subject_id" in result
        assert result["subject_id"] == "definitely-not-a-subject"

    def test_compute_face_embedding_missing_image_returns_empty(self):
        """Missing/invalid image must not crash; returns empty embedding."""
        from server import compute_face_embedding

        result = compute_face_embedding("/tmp/definitely-not-an-image.png")

        assert result == []

    def test_subject_match_missing_generated_image_graceful(self, test_image):
        """Missing generated image must not crash subject_match; returns pass=False."""
        from server import brandly_subject_save, brandly_subject_match

        brandly_subject_save(
            subject_id="test-subject-match-img",
            reference_image_path=test_image,
            name="Test Subject",
            story="A test story",
            outfit="Test outfit",
        )

        result = brandly_subject_match(
            generated_image_path="/tmp/definitely-not-an-image.png",
            subject_id="test-subject-match-img",
        )

        assert result["pass"] is False
        assert result["similarity"] == 0.0
        assert result["subject_id"] == "test-subject-match-img"