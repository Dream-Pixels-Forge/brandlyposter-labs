"""Tests for compute_similarity: zero/empty vectors must never produce NaN."""

import warnings

import numpy as np


def test_compute_similarity_zero_vector_returns_zero_not_nan():
    """Zero-vector similarity must be 0.0, never nan (no RuntimeWarning)."""
    from server import compute_similarity

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # turn RuntimeWarning into exception
        assert compute_similarity([0.0] * 512, [0.0] * 512) == 0.0
        assert compute_similarity([0.0] * 512, [1.0] * 512) == 0.0
        assert compute_similarity([], []) == 0.0


def test_compute_similarity_happy_path_unchanged():
    """Identical/orthogonal/opposite vectors still behave as before."""

    from server import compute_similarity

    assert compute_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == 1.0
    assert abs(compute_similarity([1.0, 0.0, 0.0], [0.0, 1.0, 0.0]) - 0.0) < 1e-6
    assert abs(compute_similarity([1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]) - (-1.0)) < 1e-6


def test_compute_similarity_result_is_json_safe():
    """Result must be a finite float serializable with allow_nan=False."""
    import json

    from server import compute_similarity

    s = compute_similarity([0.0] * 512, [0.0] * 512)
    assert isinstance(s, float)
    assert not np.isnan(s)
    assert not np.isinf(s)
    json.dumps({"similarity": s}, allow_nan=False)  # must not raise
