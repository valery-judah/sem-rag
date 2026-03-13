import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.anyio


async def test_global_exception_handler_returns_error_response(app: FastAPI) -> None:
    # Inject a test route into the dynamically created test app
    @app.get("/_test_crash")
    def crash() -> None:
        raise RuntimeError("simulated crash")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        response = await client.get("/_test_crash")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json"
    assert "x-request-id" in response.headers
    json_data = response.json()
    assert "detail" in json_data
    assert json_data["detail"] == "Internal server error"
