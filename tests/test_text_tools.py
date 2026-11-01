"""Tests for text and layout tools."""


class TestTextTools:
    """Test text layer and layout tools."""

    def test_set_title(self):
        """Test brandly_set_title returns correct layer spec."""
        from server import brandly_set_title

        result = brandly_set_title(
            text="MY MOVIE",
            font="Playfair Display",
            size=120,
            color="#D4AF37",
            tracking=0.12,
        )

        assert result["layer"] == "title"
        assert result["text"] == "MY MOVIE"
        assert result["font"] == "Playfair Display"
        assert result["size"] == 120
        assert result["color"] == "#D4AF37"
        assert result["tracking"] == 0.12
        assert "css" in result

    def test_set_subtitle(self):
        """Test brandly_set_subtitle returns correct layer spec."""
        from server import brandly_set_subtitle

        result = brandly_set_subtitle(
            text="THE SUBTITLE",
            font="Montserrat",
            size=24,
            color="#FFFFFF",
        )

        assert result["layer"] == "subtitle"
        assert result["text"] == "THE SUBTITLE"
        assert result["font"] == "Montserrat"

    def test_set_tagline(self):
        """Test brandly_set_tagline returns correct layer spec."""
        from server import brandly_set_tagline

        result = brandly_set_tagline(
            text="A great tagline",
            font="Inter Light",
            size=18,
            color="#E5E5E5",
        )

        assert result["layer"] == "tagline"
        assert result["text"] == "A great tagline"
        assert result["y"] == 85

    def test_set_billing_block(self):
        """Test brandly_set_billing_block returns correct layer spec."""
        from server import brandly_set_billing_block

        result = brandly_set_billing_block(
            text="COMING SOON #BRANDLYPOSTER",
            font="Univers Condensed",
            size=8,
        )

        assert result["layer"] == "billing"
        assert result["placement"] == "very_bottom"
        assert result["opacity"] == 0.8

    def test_add_text_layer(self):
        """Test brandly_add_text_layer returns custom layer spec."""
        from server import brandly_add_text_layer

        result = brandly_add_text_layer(
            text="Custom text",
            layer_id="custom-1",
            font="Inter",
            size=32,
            color="#FF0000",
            x=25,
            y=75,
            rotation=15,
        )

        assert result["layer"] == "custom-1"
        assert result["x"] == 25
        assert result["y"] == 75
        assert result["rotation"] == 15
        assert result["opacity"] == 1.0

    def test_set_text_style(self):
        """Test brandly_set_text_style returns update action."""
        from server import brandly_set_text_style

        result = brandly_set_text_style(
            layer_id="title",
            font="Bebas Neue",
            size=140,
            color="#FF0000",
        )

        assert result["action"] == "update_style"
        assert result["layer_id"] == "title"
        assert result["font"] == "Bebas Neue"
        assert result["size"] == 140
        assert result["color"] == "#FF0000"