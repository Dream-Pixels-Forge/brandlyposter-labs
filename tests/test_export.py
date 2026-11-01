"""Tests for export specs and batch export."""


class TestExport:
    """Test export specs and batch export."""

    def test_export_specs_theatrical(self):
        """Test theatrical export specs."""
        from server import brandly_export_specs

        specs = brandly_export_specs("theatrical")

        assert specs["size"] == "27x40"
        assert specs["dpi"] == 300
        assert specs["color"] == "CMYK"
        assert "pixels" in specs

    def test_export_specs_deck(self):
        """Test deck (1440x900) export specs."""
        from server import brandly_export_specs

        specs = brandly_export_specs("deck")

        assert specs["size"] == "1440x900"
        assert specs["dpi"] == 72
        assert specs["color"] == "sRGB"

    def test_export_specs_social(self):
        """Test social (2160x3240) export specs."""
        from server import brandly_export_specs

        specs = brandly_export_specs("social")

        assert specs["size"] == "2160x3240"
        assert specs["dpi"] == 72
        assert specs["color"] == "sRGB"

    def test_export_specs_story(self):
        """Test story (1080x1920) export specs."""
        from server import brandly_export_specs

        specs = brandly_export_specs("story")

        assert specs["size"] == "1080x1920"
        assert specs["dpi"] == 72
        assert specs["color"] == "sRGB"

    def test_batch_export_creates_manifest(self):
        """Test batch export creates manifest with variants."""
        import shutil

        from server import PROJECTS_DIR, ProjectManifest, brandly_batch_export

        # Clean up any existing test project
        test_project_dir = PROJECTS_DIR / "test-batch-export"
        if test_project_dir.exists():
            shutil.rmtree(test_project_dir)

        # Create a project manifest first
        project = ProjectManifest(
            project_id="test-batch-export",
            subject_id="test-subject",
            poster_id="test-poster",
            genre="thriller",
            master_prompt="Test prompt",
            qa_score="6/6",
            qa_passed=True,
        )
        project.save()

        # Run batch export
        result = brandly_batch_export(
            project_id="test-batch-export",
            formats=["theatrical", "deck", "social", "story"],
            generated_image_path="/fake/path.png",
        )

        assert result["project_id"] == "test-batch-export"
        assert "variants" in result
        assert len(result["variants"]) == 4

        # Check each variant has correct structure
        for variant in result["variants"]:
            assert "format" in variant
            assert "file" in variant
            assert "specs" in variant
            assert "path" in variant

        # Verify manifest updated
        loaded = ProjectManifest.load("test-batch-export")
        assert len(loaded.variants) == 4
        assert loaded.variants[0]["format"] == "theatrical"

        # Cleanup
        shutil.rmtree(test_project_dir)

    def test_batch_export_missing_project_graceful(self):
        """Missing project must not crash batch_export."""
        from server import brandly_batch_export

        result = brandly_batch_export(
            project_id="definitely-not-a-project",
            formats=["deck"],
        )

        assert result["pass"] is False or "error" in result
        assert "project_id" in result
        assert result["project_id"] == "definitely-not-a-project"