"""Test that server imports correctly and FastMCP instance is created."""
import pytest


def test_server_imports():
    """Test that server module imports without error."""
    from server import mcp
    assert mcp is not None
    assert hasattr(mcp, 'name')
    assert mcp.name == "BrandlyPoster-Labs Pro"


def test_genres_loaded():
    """Test that genres dictionary is loaded with expected keys."""
    from server import GENRES
    expected_genres = ["thriller", "romcom", "scifi", "action", "fashion", "horror", "epic"]
    for genre in expected_genres:
        assert genre in GENRES
        assert "name" in GENRES[genre]
        assert "palette" in GENRES[genre]
        assert "backgrounds" in GENRES[genre]
        assert "lighting" in GENRES[genre]


def test_fonts_loaded():
    """Test that fonts dictionary is loaded."""
    from server import FONTS
    assert "titles" in FONTS
    assert "subtitles" in FONTS
    assert "taglines" in FONTS
    assert "billing" in FONTS
    assert len(FONTS["titles"]) > 0


def test_subject_profile_crud():
    """Test SubjectProfile save/load."""
    from server import SubjectProfile

    subject = SubjectProfile(
        subject_id="test-subject-1",
        name="Test Subject",
        reference_images=["/path/to/ref.jpg"],
        face_embedding=[0.1] * 512,
        story="Test story",
        outfit="Test outfit",
    )
    subject.save()

    # Load back
    loaded = SubjectProfile.load("test-subject-1")
    assert loaded.subject_id == "test-subject-1"
    assert loaded.name == "Test Subject"
    assert loaded.story == "Test story"
    assert loaded.outfit == "Test outfit"
    assert loaded.face_embedding == [0.1] * 512


def test_project_manifest_crud():
    """Test ProjectManifest save/load."""
    from server import ProjectManifest

    project = ProjectManifest(
        project_id="test-project-1",
        subject_id="test-subject-1",
        poster_id="test-poster-1",
        genre="thriller",
        master_prompt="Test prompt",
    )
    project.save()

    # Load back
    loaded = ProjectManifest.load("test-project-1")
    assert loaded.project_id == "test-project-1"
    assert loaded.subject_id == "test-subject-1"
    assert loaded.genre == "thriller"
    assert loaded.master_prompt == "Test prompt"
    assert loaded.qa_score == "0/6"
    assert loaded.qa_passed is False


def test_build_master_prompt():
    """Test master prompt building includes all required elements."""
    from server import SubjectProfile, build_master_prompt

    subject = SubjectProfile(
        subject_id="test",
        name="Test",
        reference_images=[],
        face_embedding=None,
        story="Visionary leader from Kinshasa",
        outfit="ivory suit structured shoulders",
    )

    prompt = build_master_prompt(
        subject=subject,
        genre="thriller",
        title="L'ÉTOILE",
        subtitle="THE ASCENT",
        tagline="She built her own empire",
        outfit="cream linen blazer",
        fix_earrings=True,
        resolution="2:3",
    )

    # Check key elements present
    assert "L'ÉTOILE" in prompt
    assert "THE ASCENT" in prompt
    assert "She built her own empire" in prompt
    assert "gold hoop earrings" in prompt.lower()
    assert "68 percent height" in prompt
    assert "2:3" in prompt
    assert "Kinshasa" in prompt
    assert "cream linen blazer" in prompt


def test_compute_similarity():
    """Test cosine similarity computation."""

    from server import compute_similarity

    # Identical vectors
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert compute_similarity(a, b) == 1.0

    # Orthogonal vectors
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert abs(compute_similarity(a, b) - 0.0) < 1e-6

    # Opposite vectors
    a = [1.0, 0.0, 0.0]
    b = [-1.0, 0.0, 0.0]
    assert abs(compute_similarity(a, b) - (-1.0)) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])