import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_get_courses():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/courses/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Add more tests for other endpoints
