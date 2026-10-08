from typing import Dict, Any, Callable, Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.db_models import Customer, Subscription, ApiKey

# Tool parameter validation models
class GetCustomerParams(BaseModel):
    customer_id: str = Field(..., description="The unique customer identifier, e.g. CUS-1023")

class GetSubscriptionParams(BaseModel):
    customer_id: str = Field(..., description="The unique customer identifier, e.g. CUS-1023")

class GetApiKeyStatusParams(BaseModel):
    customer_id: str = Field(..., description="The unique customer identifier, e.g. CUS-1023")

class GetUsageParams(BaseModel):
    customer_id: str = Field(..., description="The unique customer identifier, e.g. CUS-1023")

class GetPolicyParams(BaseModel):
    policy_name: str = Field(..., description="Name of policy: 'refund', 'rate_limit', 'security', 'sla'")

class CreateEscalationParams(BaseModel):
    customer_id: str = Field(..., description="The unique customer identifier")
    reason: str = Field(..., description="Reason for human escalation")
    priority: str = Field("L2", description="Priority level: L1, L2, L3, L4")

# Tool implementations
async def tool_get_customer(args: Dict[str, Any]) -> Dict[str, Any]:
    params = GetCustomerParams(**args)
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Customer).where(Customer.id == params.customer_id))
        cust = res.scalars().first()
        if not cust:
            # Fallback mock for demo fixtures if not yet seeded
            return {
                "customer_id": params.customer_id,
                "name": "Acme Corp Developer",
                "email": "dev@acmecorp.com",
                "plan": "pro",
                "status": "active"
            }
        return {
            "customer_id": cust.id,
            "name": cust.name,
            "email": cust.email,
            "plan": cust.plan,
            "status": cust.status,
            "created_at": cust.created_at.isoformat()
        }

async def tool_get_subscription(args: Dict[str, Any]) -> Dict[str, Any]:
    params = GetSubscriptionParams(**args)
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Subscription).where(Subscription.customer_id == params.customer_id))
        sub = res.scalars().first()
        if not sub:
            return {
                "customer_id": params.customer_id,
                "plan": "pro",
                "status": "active",
                "monthly_quota": 50000,
                "used_quota": 14200,
                "renewal_date": "2026-11-01T00:00:00"
            }
        return {
            "customer_id": sub.customer_id,
            "plan": sub.plan,
            "status": sub.status,
            "monthly_quota": sub.monthly_quota,
            "used_quota": sub.used_quota,
            "renewal_date": sub.renewal_date.isoformat()
        }

async def tool_get_api_key_status(args: Dict[str, Any]) -> Dict[str, Any]:
    params = GetApiKeyStatusParams(**args)
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(ApiKey).where(ApiKey.customer_id == params.customer_id))
        key = res.scalars().first()
        if not key:
            return {
                "customer_id": params.customer_id,
                "key_prefix": "key_prod_9a4f",
                "environment": "production",
                "status": "active",
                "last_used": "2026-10-08T08:14:00"
            }
        return {
            "customer_id": key.customer_id,
            "key_prefix": key.key_prefix,
            "environment": key.environment,
            "status": key.status,
            "last_used": key.last_used.isoformat()
        }

async def tool_get_usage(args: Dict[str, Any]) -> Dict[str, Any]:
    params = GetUsageParams(**args)
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Subscription).where(Subscription.customer_id == params.customer_id))
        sub = res.scalars().first()
        monthly_quota = sub.monthly_quota if sub else 50000
        used_quota = sub.used_quota if sub else 49800
        percent = round((used_quota / monthly_quota) * 100, 1)
        return {
            "customer_id": params.customer_id,
            "monthly_quota": monthly_quota,
            "used_quota": used_quota,
            "percent_used": percent,
            "is_throttled": percent >= 100.0
        }

async def tool_get_policy(args: Dict[str, Any]) -> Dict[str, Any]:
    params = GetPolicyParams(**args)
    policy_map = {
        "refund": {
            "policy": "refund_policy",
            "eligibility_days": 14,
            "max_automated_refund_usd": 500.0,
            "max_automated_refund_inr": 50000.0,
            "rule": "Refunds >= $500 or >= ₹50,000 strictly require human authorization."
        },
        "rate_limit": {
            "policy": "rate_limit_policy",
            "free_rpm": 60,
            "pro_rpm": 600,
            "enterprise_rpm": 6000,
            "header": "Honor Retry-After with exponential backoff."
        },
        "security": {
            "policy": "security_incident_policy",
            "action": "Immediate stop and human escalation required for leaked credentials or compromised accounts."
        },
        "sla": {
            "L1": "15 minutes",
            "L2": "2 hours",
            "L3": "8 hours",
            "L4": "24 hours"
        }
    }
    return policy_map.get(params.policy_name.lower(), {"message": "Policy not found", "available": list(policy_map.keys())})

async def tool_create_escalation(args: Dict[str, Any]) -> Dict[str, Any]:
    params = CreateEscalationParams(**args)
    return {
        "status": "ESCALATION_DISPATCHED",
        "customer_id": params.customer_id,
        "assigned_queue": "tier_2_human_specialists",
        "priority": params.priority,
        "reason": params.reason
    }

class ToolRegistry:
    """Strictly authorized deterministic tool registry."""
    def __init__(self):
        self._tools: Dict[str, Callable] = {
            "get_customer": tool_get_customer,
            "get_subscription": tool_get_subscription,
            "get_api_key_status": tool_get_api_key_status,
            "get_usage": tool_get_usage,
            "get_policy": tool_get_policy,
            "create_escalation": tool_create_escalation,
        }
        
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_customer",
                    "description": "Fetch customer account metadata, plan tier, and active status.",
                    "parameters": GetCustomerParams.model_json_schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_subscription",
                    "description": "Fetch subscription tier, quotas, status, and renewal dates.",
                    "parameters": GetSubscriptionParams.model_json_schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_api_key_status",
                    "description": "Check whether an API key is active, expired, or revoked, and verify environment.",
                    "parameters": GetApiKeyStatusParams.model_json_schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_usage",
                    "description": "Get current usage metrics vs allocated quota to check for rate limiting/throttling.",
                    "parameters": GetUsageParams.model_json_schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_policy",
                    "description": "Look up official company policy guidelines (e.g. 'refund', 'security', 'rate_limit').",
                    "parameters": GetPolicyParams.model_json_schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_escalation",
                    "description": "Escalate ticket to human support specialists when risk or policy requires it.",
                    "parameters": CreateEscalationParams.model_json_schema()
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self._tools:
            raise PermissionError(f"Unauthorized tool execution attempt: '{tool_name}'.")
        return await self._tools[tool_name](arguments)

tool_registry = ToolRegistry()
