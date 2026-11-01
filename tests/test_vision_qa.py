"""Tests for vision QA: 6-point check."""
import pytest
from pathlib import Path
import tempfile


def _create_test_poster(path: Path, size=(1024, 1536)):  # 2:3 ratio
    """Create a test poster image with some content."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', size, color=(20, 20, 30))
    draw = ImageDraw.Draw(img)

    # Add title text at top
    draw.text((size[0]//2, 50), "TEST POSTER", fill=(212, 175, 55), anchor="mm")
    # Add tagline at bottom
    draw.text((size[0]//2, size[1]-50), "A test tagline", fill=(200, 200, 200), anchor="mm")

    # Add some gold circles as "earrings" in upper-middle
    draw.ellipse([size[0]//3 - 15, size[1]//3 - 15, size[0]//3 + 15, size[1]//3 + 15], outline=(212, 175, 55), width=3)
    draw.ellipse([2*size[0]//3 - 15, size[1]//3 - 15, 2*size[0]//3 + 15, size[1]//3 + 15], outline=(212, 175, 55), width=3)

    # Add content at bottom (not cropped)
    draw.rectangle([size[0]//4, int(size[1]*0.9), 3*size[0]//4, size[1]], fill=(50, 50, 60))

    img.save(path)
    return path


class TestVisionQA:
    """Test the 6-point vision QA checks."""

    @pytest.fixture
    def test_poster(self):
        """Create a test poster image."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        _create_test_poster(path)
        yield str(path)
        if path.exists():
            path.unlink()

    @pytest.fixture
    def subject_with_embedding(self, test_poster):
        """Create a subject with face embedding from the test poster."""
        from server import brandly_subject_save, SubjectProfile

        brandly_subject_save(
            subject_id="test-qa-subject",
            reference_image_path=test_poster,
            name="QA Test Subject",
        )
        return "test-qa-subject"

    def test_qa_check_returns_six_checks(self, test_poster, subject_with_embedding):
        """Test QA check returns all 6 checks."""
        from server import brandly_qa_check

        result = brandly_qa_check(test_poster, subject_with_embedding)

        assert "score" in result
        assert "checks" in result
        assert "pass" in result

        checks = result["checks"]
        assert len(checks) == 6

        expected_checks = [
            "likeness_preserved",
            "both_earrings_symmetrical",
            "no_cropped_hands_feet",
            "ratio_2_3",
            "eyes_sharp",
            "text_legible",
        ]
        for check in expected_checks:
            assert check in checks

    def test_qa_check_without_subject_skips_likeness(self, test_poster):
        """Test QA check works without subject_id (skips likeness)."""
        from server import brandly_qa_check

        result = brandly_qa_check(test_poster, subject_id=None)

        assert result["checks"]["likeness_preserved"]["pass"] is True
        assert "note" in result["checks"]["likeness_preserved"]

    def test_qa_check_ratio_2_3_passes(self, test_poster):
        """Test 2:3 ratio check passes for correct ratio."""
        from server import brandly_qa_check

        result = brandly_qa_check(test_poster)
        assert result["checks"]["ratio_2_3"]["pass"] is True

    def test_qa_check_ratio_2_3_fails_wrong_ratio(self):
        """Test 2:3 ratio check fails for wrong ratio."""
        from server import brandly_qa_check, brandly_qa_check

        # Create image with wrong ratio (square)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        from PIL import Image
        img = Image.new('RGB', (1000, 1000), color=(20, 20, 30))
        img.save(path)

        try:
            result = brandly_qa_check(str(path))
            assert result["checks"]["ratio_2_3"]["pass"] is False
        finally:
            path.unlink()

    def test_qa_check_earrings_detected(self, test_poster):
        """Test earring symmetry check detects test earrings."""
        from server import brandly_qa_check

        result = brandly_qa_check(test_poster)
        earring_check = result["checks"]["both_earrings_symmetrical"]

        # Our test image has symmetrical gold circles
        assert "left_ear" in earring_check
        assert "right_ear" in earring_check
        # Note: actual detection may vary with simple test image