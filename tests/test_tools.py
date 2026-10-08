import pytest
from app.tools.registry import tool_registry

@pytest.mark.asyncio
async def test_get_customer_tool():
    res = await tool_registry.execute_tool("get_customer", {"customer_id": "CUS-1023"})
    assert res is not None
    assert res["customer_id"] == "CUS-1023"
    assert "plan" in res

@pytest.mark.asyncio
async def test_get_api_key_status_tool():
    res = await tool_registry.execute_tool("get_api_key_status", {"customer_id": "CUS-1023"})
    assert res is not None
    assert res["status"] in ["active", "revoked", "expired"]
    assert "environment" in res

@pytest.mark.asyncio
async def test_unauthorized_tool_rejected():
    with pytest.raises(PermissionError):
        await tool_registry.execute_tool("drop_database_tables", {"confirm": True})
