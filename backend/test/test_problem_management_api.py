"""
跨模块问题管理共享元数据 API 测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_problem_management_catalog_requires_auth(async_client: AsyncClient):
    """未登录时不应访问问题管理共享字典"""

    response = await async_client.get("/api/v1/problem-management/catalog")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_problem_management_catalog_returns_confirmed_metadata(
    async_client: AsyncClient,
    test_user_token: str,
):
    """已登录时应返回当前已确认的问题管理元数据"""

    headers = {"Authorization": f"Bearer {test_user_token}"}

    response = await async_client.get(
        "/api/v1/problem-management/catalog",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["response_modes"] == ["brief", "eight_d"]
    assert data["handling_levels"] == ["simple", "complex", "major"]
    assert data["numbering_rule"]["issue_prefix"] == "ZXQ"
    assert data["numbering_rule"]["report_prefix"] == "ZX8D"
    assert data["numbering_rule"]["issue_pattern"] == "ZXQ-<分类子类>-<YYMM>-<SEQ3>"
    assert any(item["key"] == "CQ1" and item["label"] == "售后" for item in data["categories"])
    assert any(item["key"] == "AQ3" and item["label"] == "客户审核问题" for item in data["categories"])
