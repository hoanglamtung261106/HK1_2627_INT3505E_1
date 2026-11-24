def v1_create_order(body):
    return {
        "handler": "v1",
        "order_id": "ord_v1_001",
        "account_id": body.get("account_id", ""),
        "status": "created",
    }


def v2_create_order(body):
    return {
        "handler": "v2",
        "order_id": "ord_v2_001",
        "account_id": body.get("account_id", ""),
        "status": "pending_fulfillment",
        "items": body.get("items", []),
    }
