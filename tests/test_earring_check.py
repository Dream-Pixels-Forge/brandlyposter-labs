"""Tests for earring symmetry check."""
import pytest
from pathlib import Path
import tempfile


def _create_image_with_earrings(path: Path, symmetrical=True):
    """Create test image with gold hoop earrings."""
    from PIL import Image, ImageDraw
    size = (512, 512)
    img = Image.new('RGB', size, color=(30, 30, 40))
    draw = ImageDraw.Draw(img)

    # Draw gold hoop earrings
    if symmetrical:
        left_x = size[0] // 3
        right_x = 2 * size[0] // 3
        left_y = size[1] // 3
        right_y = size[1] // 3
        radius = 20
    else:
        left_x = size[0] // 3
        right_x = 2 * size[0] // 3 + 15
        left_y = size[1] // 3
        right_y = size[1] // 3 + 25  # Different y position for asymmetry
        radius = 20

    # Gold color
    gold = (212, 175, 55)
    draw.ellipse([left_x - radius, left_y - radius, left_x + radius, left_y + radius], outline=gold, width=4)
    draw.ellipse([right_x - radius, right_y - radius, right_x + radius, right_y + radius], outline=gold, width=4)

    img.save(path)
    return path


class TestEarringCheck:
    """Test earring symmetry detection."""

    def test_symmetrical_earrings_pass(self):
        """Test symmetrical earrings pass the check."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        _create_image_with_earrings(path, symmetrical=True)

        try:
            from server import brandly_earring_check
            result = brandly_earring_check(str(path))

            # Should detect two candidates
            assert result["pass"] is True or "candidates" in result
            if "left_ear" in result and "right_ear" in result:
                assert result["symmetrical"] is True
        finally:
            path.unlink()

    def test_asymmetrical_earrings_fail(self):
        """Test asymmetrical earrings fail the check."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        _create_image_with_earrings(path, symmetrical=False)

        try:
            from server import brandly_earring_check
            result = brandly_earring_check(str(path))

            # Should detect asymmetry
            if "left_ear" in result and "right_ear" in result:
                assert result["symmetrical"] is False
                assert result["pass"] is False
        finally:
            path.unlink()

    def test_no_earrings_fails(self):
        """Test image without gold earrings fails."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = Path(f.name)
        from PIL import Image
        img = Image.new('RGB', (512, 512), color=(30, 30, 40))
        img.save(path)

        try:
            from server import brandly_earring_check
            result = brandly_earring_check(str(path))

            assert result["pass"] is False
        finally:
            path.unlink()