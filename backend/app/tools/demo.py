from decimal import Decimal
from typing import Any

from app.tools.schemas import (
    FetchUrlArguments,
    GetCustomerArguments,
    IssueRefundArguments,
    SendEmailArguments,
)

DEMO_CUSTOMERS = {
    "1001": {"id": "1001", "name": "Avery Chen", "tier": "standard"},
    "1002": {"id": "1002", "name": "Morgan Silva", "tier": "premium"},
}
DEMO_ORDERS = {"ORD-1001": Decimal("49.99"), "ORD-1002": Decimal("125.00")}
DEMO_URLS = {
    "https://docs.agentshield.local/": {
        "status_code": 200,
        "title": "AgentShield demo documentation",
    },
    "https://status.agentshield.local/": {
        "status_code": 200,
        "title": "All demo systems operational",
    },
}


def get_customer(arguments: GetCustomerArguments) -> dict[str, Any]:
    customer = DEMO_CUSTOMERS.get(arguments.customer_id)
    if customer is None:
        return {"found": False, "customer_id": arguments.customer_id}
    return {"found": True, "customer": customer}


def send_email(arguments: SendEmailArguments) -> dict[str, Any]:
    return {
        "accepted": True,
        "delivery": "simulated",
        "to": arguments.to,
        "message_preview": arguments.message[:80],
    }


def issue_refund(arguments: IssueRefundArguments) -> dict[str, Any]:
    maximum = DEMO_ORDERS.get(arguments.order_id)
    if maximum is None:
        return {"issued": False, "reason": "demo order not found"}
    if arguments.amount > maximum:
        return {"issued": False, "reason": "amount exceeds demo order total"}
    return {
        "issued": True,
        "processing": "simulated",
        "order_id": arguments.order_id,
        "amount": str(arguments.amount),
    }


def fetch_url(arguments: FetchUrlArguments) -> dict[str, Any]:
    normalized_url = str(arguments.url)
    fixture = DEMO_URLS.get(normalized_url)
    if fixture is None:
        return {
            "fetched": False,
            "url": normalized_url,
            "reason": "only allowlisted demo URLs are available",
        }
    return {"fetched": True, "url": normalized_url, **fixture}
