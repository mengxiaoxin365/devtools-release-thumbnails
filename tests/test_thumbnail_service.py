import pytest

from src.thumbnail_service import ThumbnailRequest, choose_dimensions


def test_thumbnail_decision_preserves_requested_card_bounds():
    request = ThumbnailRequest("release.png", b"pixels", target_width=800, target_height=450)
    assert choose_dimensions(request) == (800, 450)


def test_thumbnail_decision_rejects_zero_dimension():
    with pytest.raises(ValueError):
        choose_dimensions(ThumbnailRequest("release.png", b"pixels", target_width=0))
