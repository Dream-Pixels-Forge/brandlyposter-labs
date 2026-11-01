"""Tests for animation tools."""
import pytest


class TestAnimation:
    """Test animation tools."""

    def test_animate_poster_parallax(self):
        """Test parallax animation preset."""
        from server import brandly_animate_poster

        result = brandly_animate_poster(animation_type="parallax", duration=6, fps=24)

        assert result["animation_type"] == "parallax"
        assert result["duration"] == 6
        assert result["fps"] == 24
        assert result["loop"] is True
        assert "keyframes" in result
        assert result["keyframes"]["bg_move"] == "slow pan"

    def test_animate_poster_title_reveal(self):
        """Test title reveal animation preset."""
        from server import brandly_animate_poster

        result = brandly_animate_poster(animation_type="title_reveal")

        assert result["animation_type"] == "title_reveal"
        assert result["keyframes"]["title"] == "gold shimmer reveal from left"

    def test_animate_poster_ken_burns(self):
        """Test ken burns animation preset."""
        from server import brandly_animate_poster

        result = brandly_animate_poster(animation_type="ken_burns")

        assert result["keyframes"]["hero"] == "slow zoom in"
        assert result["keyframes"]["bg"] == "slow zoom out"

    def test_animate_poster_full_cinematic(self):
        """Test full cinematic animation preset."""
        from server import brandly_animate_poster

        result = brandly_animate_poster(animation_type="full_cinematic")

        assert "sequence" in result["keyframes"]
        assert len(result["keyframes"]["sequence"]) == 5

    def test_animate_poster_unknown_type_defaults(self):
        """Test unknown animation type defaults to parallax."""
        from server import brandly_animate_poster

        result = brandly_animate_poster(animation_type="unknown_type")

        assert result["animation_type"] == "unknown_type"
        assert result["keyframes"]["bg_move"] == "slow pan"

    def test_set_animation_keyframes(self):
        """Test brandly_set_animation_keyframes."""
        from server import brandly_set_animation_keyframes

        keyframes = [
            {"time": 0, "x": 50, "y": 50, "scale": 1.0, "opacity": 0},
            {"time": 50, "x": 50, "y": 50, "scale": 1.1, "opacity": 1},
            {"time": 100, "x": 50, "y": 50, "scale": 1.0, "opacity": 1},
        ]

        result = brandly_set_animation_keyframes("title", keyframes)

        assert result["layer_id"] == "title"
        assert result["keyframes"] == keyframes

    def test_export_animation(self):
        """Test brandly_export_animation returns specs."""
        from server import brandly_export_animation

        result = brandly_export_animation(
            format="mp4",
            resolution="1080x1920",
            fps=24,
            duration=6,
        )

        assert result["format"] == "mp4"
        assert result["resolution"] == "1080x1920"
        assert result["fps"] == 24
        assert result["duration"] == 6
        assert result["codec"] == "h264"
        assert "file" in result