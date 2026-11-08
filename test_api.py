import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


tests = [
    (1,  "Health check",                "GET",    "/health", None, 200),
    (2,  "List products",               "GET",    "/products", None, 200),
    (3,  "Add valid product",           "POST",   "/products", {"product_name": "Keyboard", "category": "Electronics"}, 201),
    (4,  "Add invalid product",         "POST",   "/products", {"product_name": "", "category": "Electronics"}, 400),
    (5,  "Get missing product",         "GET",    "/products/999", None, 404),
    (6,  "Add valid order",             "POST",   "/orders", {"order_date": "2026-06-01", "order_status": "Completed", "region": "North"}, 201),
    (7,  "Bad date format",             "POST",   "/orders", {"order_date": "01-06-2026", "order_status": "Completed", "region": "North"}, 400),
    (8,  "Bad order status",            "POST",   "/orders", {"order_date": "2026-06-01", "order_status": "Pending", "region": "North"}, 400),
    (9,  "Add valid order item",        "POST",   "/order-items", {"order_id": 1, "product_id": 1, "quantity": 2, "unit_price": 599}, 201),
    (10, "Quantity zero (boundary)",    "POST",   "/order-items", {"order_id": 1, "product_id": 1, "quantity": 0, "unit_price": 599}, 400),
    (11, "Negative price",              "POST",   "/order-items", {"order_id": 1, "product_id": 1, "quantity": 2, "unit_price": -5}, 400),
    (12, "Nonexistent product (FK)",    "POST",   "/order-items", {"order_id": 1, "product_id": 999, "quantity": 2, "unit_price": 599}, 400),
    (13, "Update order status",         "PUT",    "/orders/1", {"order_status": "Returned"}, 200),
    (14, "Delete product in use",       "DELETE", "/products/1", None, 409),
]

passed = 0
for num, name, method, path, body, expected in tests:
    status, text = call(method, path, body)
    ok = status == expected
    passed += ok
    print(f"Test {num:>2} | {name:<28} | {method:<6} {path:<14} | "
          f"expected {expected}, got {status} | {'PASS' if ok else 'FAIL'}")
    print(f"         response: {text.strip()[:120]}")

call("PUT", "/orders/1", {"order_status": "Completed"})  # restore order 1
print(f"\n{passed} of {len(tests)} tests passed")