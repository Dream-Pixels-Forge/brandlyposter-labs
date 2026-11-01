"""Tests for create_poster tool."""
import tempfile
from pathlib import Path

import pytest


def _create_test_image(path: Path):
    """Create a simple test image."""
    from PIL import Image
    img = Image.new('RGB', (512, 512), color=(100, 100, 120))
    img.save(path)


class TestCreatePoster:
    """Test brandly_create_poster tool."""

    @pytest.fixture
    def subject_with_image(self):
        """Create a subject with a test reference image."""
        from server import brandly_subject_save

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            ref_path = Path(f.name)
        _create_test_image(ref_path)

        brandly_subject_save(
            subject_id="test-create-poster",
            reference_image_path=str(ref_path),
            name="Create Poster Test",
            story="A visionary leader from Kinshasa who built her empire",
            outfit="ivory suit structured shoulders",
        )

        yield "test-create-poster"

        # Cleanup
        ref_path.unlink(missing_ok=True)

    def test_create_poster_returns_master_prompt(self, subject_with_image):
        """Test create_poster returns master prompt with all elements."""
        from server import brandly_create_poster

        result = brandly_create_poster(
            subject_id=subject_with_image,
            genre="thriller",
            title="L'ÉTOILE",
            subtitle="THE ASCENT",
            tagline="She built her own empire",
        )

        assert "master_prompt" in result
        assert "genre_config" in result
        assert "subject_id" in result
        assert "qa_checklist" in result
        assert "variant_plan" in result

        prompt = result["master_prompt"]
        assert "L'ÉTOILE" in prompt
        assert "THE ASCENT" in prompt
        assert "She built her own empire" in prompt
        assert "gold hoop earrings" in prompt.lower()
        assert "68 percent height" in prompt
        assert "2:3" in prompt

    def test_create_poster_earring_fix_enforced(self, subject_with_image):
        """Test earring fix is enforced when fix_earrings=True."""
        from server import brandly_create_poster

        result = brandly_create_poster(
            subject_id=subject_with_image,
            genre="thriller",
            title="TEST",
            fix_earrings=True,
        )

        assert "gold hoop earrings" in result["master_prompt"].lower()
        assert "symmetrical" in result["master_prompt"].lower()

        # Check qa_checklist includes earring check
        assert any("earring" in c.lower() for c in result["qa_checklist"])

    def test_create_poster_earring_fix_skipped(self, subject_with_image):
        """Test earring fix is skipped when fix_earrings=False."""
        from server import brandly_create_poster

        result = brandly_create_poster(
            subject_id=subject_with_image,
            genre="thriller",
            title="TEST",
            fix_earrings=False,
        )

        assert "gold hoop earrings" not in result["master_prompt"].lower()
        # qa_checklist should mention earring check is skipped
        assert any("skipped" in c.lower() for c in result["qa_checklist"])

    def test_create_poster_uses_subject_story_outfit(self, subject_with_image):
        """Test create_poster uses subject's story/outfit when not overridden."""
        from server import brandly_create_poster

        result = brandly_create_poster(
            subject_id=subject_with_image,
            genre="thriller",
            title="TEST",
        )

        prompt = result["master_prompt"]
        assert "visionary leader from Kinshasa" in prompt
        assert "ivory suit structured shoulders" in prompt

    def test_create_poster_overrides_story_outfit(self, subject_with_image):
        """Test create_poster allows overriding story/outfit."""
        from server import brandly_create_poster

        result = brandly_create_poster(
            subject_id=subject_with_image,
            genre="thriller",
            title="TEST",
            story="Custom story override",
            outfit="custom outfit override",
        )

        prompt = result["master_prompt"]
        assert "Custom story override" in prompt
        assert "custom outfit override" in prompt
        assert "visionary leader from Kinshasa" not in prompt
        assert "ivory suit" not in prompt

    def test_create_poster_variant_plan(self, subject_with_image):
        """Test variant plan includes all parameters."""
        from server import brandly_create_poster

        result = brandly_create_poster(
            subject_id=subject_with_image,
            genre="romcom",
            title="LOVE IN KIN",
            subtitle="CHAOS & CHEMISTRY",
            tagline="Boss by day. Hopeless romantic by night.",
            resolution="2:3",
        )

        plan = result["variant_plan"]
        assert plan["title"] == "LOVE IN KIN"
        assert plan["subtitle"] == "CHAOS & CHEMISTRY"
        assert plan["tagline"] == "Boss by day. Hopeless romantic by night."
        assert plan["genre"] == "romcom"
        assert plan["resolution"] == "2:3"

    def test_create_poster_missing_subject_graceful(self):
        """Missing subject must not crash create_poster."""
        from server import brandly_create_poster

        result = brandly_create_poster(
            subject_id="definitely-not-a-subject",
            genre="thriller",
            title="TEST",
        )

        assert result["pass"] is False or "error" in result
        assert "subject_id" in result
        assert result["subject_id"] == "definitely-not-a-subject"