from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


def test_unsupported_png_is_rejected_over_real_http_stack(e2e_stack) -> None:
    with e2e_stack.client() as client:
        response = client.post(
            "/documents",
            data={"workspace_id": "ws-e2e", "title": "Unsupported"},
            files={"file": ("image.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )

    assert response.status_code == 415
    assert "text-based PDF and Markdown" in response.json()["detail"]
