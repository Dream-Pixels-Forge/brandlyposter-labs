"""Tests for comprehensive fix tools and scan issues."""
import tempfile
from pathlib import Path

import pytest


def _create_test_poster(path: Path, size=(1024, 1536)):
    """Create a test poster image with some content."""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', size, color=(20, 20, 30))
    draw = ImageDraw.Draw(img)

    # Add title text at top
    draw.text((size[0]//2, 50), "TEST POSTER", fill=(212, 175, 55), anchor="mm")
    # Add tagline at bottom
    draw.text((size[0]//2, size[1]-50), "A test tagline", fill=(200, 200, 200), anchor="mm")

    # Add gold circles as "earrings" in upper-middle
    draw.ellipse([size[0]//3 - 15, size[1]//3 - 15, size[0]//3 + 15, size[1]//3 + 15], outline=(212, 175, 55), width=3)
    draw.ellipse([2*size[0]//3 - 15, size[1]//3 - 15, 2*size[0]//3 + 15, size[1]//3 + 15], outline=(212, 175, 55), width=3)

    # Add content at bottom (not cropped)
    draw.rectangle([size[0]//4, int(size[1]*0.9), 3*size[0]//4, size[1]], fill=(50, 50, 60))

    img.save(path)
    return path


class TestScanIssues:
    """Test comprehensive scan issues detection."""

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
        from server import brandly_subject_save

        brandly_subject_save(
            subject_id="test-scan-subject",
            reference_image_path=test_poster,
            name="Scan Test Subject",
        )
        return "test-scan-subject"

    def test_scan_issues_returns_all_categories(self, test_poster, subject_with_embedding):
        """Test scan_issues returns all detection categories."""
        from server import brandly_scan_issues

        result = brandly_scan_issues(test_poster, subject_with_embedding)

        assert 'issues' in result
        assert 'scan_frames' in result
        assert 'annotated_image_path' in result
        assert 'summary' in result
        assert 'fix_prompt' in result
        assert 'fix_categories' in result

        issues = result['issues']
        # Check key categories exist
        expected_categories = ['earrings', 'likeness', 'cropping', 'ratio', 'eye_sharpness', 'text', 'wardrobe', 'props', 'background', 'lighting', 'artifacts']
        for cat in expected_categories:
            assert cat in issues, f"Missing category: {cat}"

    def test_scan_issues_summary_structure(self, test_poster):
        """Test scan_issues summary has correct structure."""
        from server import brandly_scan_issues

        result = brandly_scan_issues(test_poster)

        summary = result['summary']
        assert 'total_checks' in summary
        assert 'passed' in summary
        assert 'failed' in summary
        assert 'critical' in summary
        assert 'high' in summary
        assert 'medium' in summary
        assert 'low' in summary

    def test_scan_issues_creates_annotated_image(self, test_poster):
        """Test scan_issues creates annotated image file."""
        from server import brandly_scan_issues

        result = brandly_scan_issues(test_poster)
        annotated_path = result['annotated_image_path']

        assert annotated_path != test_poster
        assert Path(annotated_path).exists()

    def test_scan_frames_have_correct_structure(self, test_poster):
        """Test scan_frames have correct structure for animation."""
        from server import brandly_scan_issues

        result = brandly_scan_issues(test_poster)
        frames = result['scan_frames']

        assert len(frames) > 0
        for frame in frames:
            assert 'region' in frame
            assert 'bbox' in frame
            assert 'issue' in frame
            assert 'severity' in frame
            assert len(frame['bbox']) == 4  # x, y, w, h

    def test_scan_issues_missing_subject_records_likeness_fail(self, test_poster):
        """Missing subject must not crash; likeness recorded as pass=False (not silently dropped)."""
        from server import brandly_scan_issues

        result = brandly_scan_issues(test_poster, subject_id="definitely-not-a-subject")

        issues = result['issues']
        assert 'likeness' in issues, "likeness check must not be silently dropped for missing subject"
        assert issues['likeness']['pass'] is False
        assert 'reason' in issues['likeness']

    def test_detect_issues_missing_subject_records_likeness_fail(self, test_poster):
        """detect_issues_with_visualization with missing subject: likeness pass=False, no silent drop."""
        from server import detect_issues_with_visualization

        result = detect_issues_with_visualization(test_poster, subject_id="definitely-not-a-subject")

        issues = result['issues']
        assert 'likeness' in issues, "likeness check must not be silently dropped for missing subject"
        assert issues['likeness']['pass'] is False
        assert 'reason' in issues['likeness']

    def test_scan_with_animation_frames(self, test_poster):
        """Test scan_issues with create_animation=True creates animation frames."""
        from server import brandly_scan_issues

        with tempfile.TemporaryDirectory() as tmpdir:
            result = brandly_scan_issues(
                test_poster,
                create_animation=True,
                animation_output_dir=tmpdir
            )

            assert 'animation_frames' in result
            assert len(result['animation_frames']) > 0
            for frame_path in result['animation_frames']:
                assert Path(frame_path).exists()


class TestFixEarringsPrompt:
    """Test earring-specific fix prompt generation."""

    def test_fix_earrings_prompt_ok_when_symmetrical(self):
        """Test fix_earrings_prompt returns ok when earrings are symmetrical."""
        from PIL import Image, ImageDraw

        from server import brandly_fix_earrings_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        
        # Create symmetrical earrings
        img = Image.new('RGB', (512, 512), color=(30, 30, 40))
        draw = ImageDraw.Draw(img)
        gold = (212, 175, 55)
        draw.ellipse([150, 150, 190, 190], outline=gold, width=4)
        draw.ellipse([320, 150, 360, 190], outline=gold, width=4)
        img.save(path)

        try:
            result = brandly_fix_earrings_prompt(str(path))
            assert result['status'] == 'ok'
            assert result['fix_prompt'] == ''
        finally:
            path.unlink()

    def test_fix_earrings_prompt_fix_needed_when_asymmetrical(self):
        """Test fix_earrings_prompt returns fix when earrings are asymmetrical."""
        from PIL import Image, ImageDraw

        from server import brandly_fix_earrings_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        
        # Create asymmetrical earrings (different positions)
        img = Image.new('RGB', (512, 512), color=(30, 30, 40))
        draw = ImageDraw.Draw(img)
        gold = (212, 175, 55)
        draw.ellipse([150, 150, 190, 190], outline=gold, width=4)
        draw.ellipse([340, 180, 380, 220], outline=gold, width=4)  # Different position
        img.save(path)

        try:
            result = brandly_fix_earrings_prompt(str(path))
            assert result['status'] == 'fix_needed'
            assert 'fix_prompt' in result
            assert 'gold hoop' in result['fix_prompt'].lower()
            assert 'symmetrical' in result['fix_prompt'].lower()
        finally:
            path.unlink()


class TestFixWardrobePrompt:
    """Test wardrobe fix prompt generation."""

    def test_fix_wardrobe_prompt_returns_structure(self):
        """Test fix_wardrobe_prompt returns expected structure."""
        from PIL import Image

        from server import brandly_fix_wardrobe_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        img = Image.new('RGB', (512, 512), color=(30, 30, 40))
        img.save(path)

        try:
            result = brandly_fix_wardrobe_prompt(str(path), expected_outfit="ivory suit structured shoulders")

            assert result['status'] == 'check_needed'
            assert result['issue'] == 'wardrobe_verification'
            assert result['expected_outfit'] == "ivory suit structured shoulders"
            assert 'fix_prompt' in result
            assert 'ivory suit' in result['fix_prompt']
            assert 'WARDROBE FIX' in result['fix_prompt']
        finally:
            path.unlink()


class TestFixPropsPrompt:
    """Test props fix prompt generation."""

    def test_fix_props_prompt_returns_structure(self):
        """Test fix_props_prompt returns expected structure."""
        from PIL import Image

        from server import brandly_fix_props_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        img = Image.new('RGB', (512, 512), color=(30, 30, 40))
        img.save(path)

        try:
            result = brandly_fix_props_prompt(str(path), expected_props=["briefcase", "smartphone"])

            assert result['status'] == 'check_needed'
            assert result['issue'] == 'props_verification'
            assert result['expected_props'] == ["briefcase", "smartphone"]
            assert 'fix_prompt' in result
            assert 'briefcase' in result['fix_prompt']
            assert 'smartphone' in result['fix_prompt']
        finally:
            path.unlink()


class TestFixBackgroundPrompt:
    """Test background fix prompt generation."""

    def test_fix_background_prompt_returns_genre_config(self):
        """Test fix_background_prompt returns genre-specific config."""
        from PIL import Image

        from server import brandly_fix_background_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        img = Image.new('RGB', (512, 512), color=(30, 30, 40))
        img.save(path)

        try:
            result = brandly_fix_background_prompt(str(path), genre="romcom")

            assert result['status'] == 'check_needed'
            assert result['issue'] == 'background_verification'
            assert result['genre'] == 'romcom'
            assert 'genre_config' in result
            assert 'fix_prompt' in result
            assert 'romcom' in result['fix_prompt'].lower() or 'Rom-Com' in result['fix_prompt']
        finally:
            path.unlink()


class TestFixLightingPrompt:
    """Test lighting fix prompt generation."""

    def test_fix_lighting_prompt_returns_balance_score(self):
        """Test fix_lighting_prompt returns balance score."""
        from PIL import Image

        from server import brandly_fix_lighting_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        img = Image.new('RGB', (512, 512), color=(100, 100, 100))
        img.save(path)

        try:
            result = brandly_fix_lighting_prompt(str(path))

            assert 'balance_score' in result
            assert 'fix_prompt' in result
            assert isinstance(result['balance_score'], float)
        finally:
            path.unlink()


class TestFixCompositionPrompt:
    """Test composition fix prompt generation."""

    def test_fix_composition_prompt_ok_for_correct_ratio(self):
        """Test fix_composition_prompt returns ok for correct 2:3 ratio."""
        from PIL import Image

        from server import brandly_fix_composition_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        # 2:3 ratio
        img = Image.new('RGB', (1024, 1536), color=(30, 30, 40))
        img.save(path)

        try:
            result = brandly_fix_composition_prompt(str(path))
            assert result['status'] == 'ok'
            assert abs(result['ratio'] - 2/3) < 0.02
        finally:
            path.unlink()

    def test_fix_composition_prompt_fix_needed_for_wrong_ratio(self):
        """Test fix_composition_prompt returns fix for wrong ratio."""
        from PIL import Image

        from server import brandly_fix_composition_prompt

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        # Square ratio (wrong)
        img = Image.new('RGB', (1000, 1000), color=(30, 30, 40))
        img.save(path)

        try:
            result = brandly_fix_composition_prompt(str(path))
            assert result['status'] == 'fix_needed'
            assert len(result['issues']) > 0
            assert any('RATIO' in issue for issue in result['issues'])
        finally:
            path.unlink()


class TestGenerateMasterFixPrompt:
    """Test comprehensive master fix prompt generation."""

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
        """Create a subject with face embedding."""
        from server import brandly_subject_save
        brandly_subject_save(
            subject_id="test-master-fix",
            reference_image_path=test_poster,
            name="Master Fix Test",
        )
        return "test-master-fix"

    def test_generate_master_fix_prompt_returns_all_fixes(self, test_poster, subject_with_embedding):
        """Test master fix prompt includes all individual fixes."""
        from server import brandly_generate_master_fix_prompt

        result = brandly_generate_master_fix_prompt(
            test_poster,
            subject_id=subject_with_embedding,
            genre="thriller",
            expected_outfit="ivory suit structured shoulders",
            expected_props=["briefcase"]
        )

        assert 'master_fix_prompt' in result
        assert 'scan_result' in result
        assert 'individual_fixes' in result
        assert 'summary' in result

        individual = result['individual_fixes']
        assert 'earrings' in individual
        assert 'wardrobe' in individual
        assert 'props' in individual
        assert 'background' in individual
        assert 'lighting' in individual
        assert 'composition' in individual


if __name__ == "__main__":
    pytest.main([__file__, "-v"])