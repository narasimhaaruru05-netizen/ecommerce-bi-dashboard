import datetime as dt
from decimal import Decimal
import kpi


# ---------- a tiny fake database (so no MySQL is needed) ----------
class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, query):
        pass

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self, dictionary=True):
        return FakeCursor(self.rows)

    def close(self):
        pass


def row(order_id, date, status, region, category, qty, price, disc, ret):
    return {"order_id": order_id, "order_date": dt.date.fromisoformat(date),
            "order_status": status, "region": region, "category": category,
            "quantity": qty, "unit_price": Decimal(price),
            "discount": Decimal(disc), "return_amount": Decimal(ret)}


def load_with(rows):
    kpi.get_connection = lambda: FakeConnection(rows)
    return kpi.load_data()


# ---------- small sample you can check by hand ----------
SAMPLE = [
    row(1, "2026-01-10", "Completed", "North", "Electronics", 2, "100", "10", "0"),   # 190
    row(1, "2026-01-10", "Completed", "North", "Clothing",    1, "50",  "0",  "0"),   # 50
    row(2, "2026-01-20", "Completed", "South", "Clothing",    3, "20",  "0",  "0"),   # 60
    row(3, "2026-02-05", "Cancelled", "East",  "Home",        5, "100", "0",  "0"),   # ignored
    row(4, "2026-02-15", "Returned",  "West",  "Home",        1, "500", "0",  "500"), # net 0
    row(5, "2026-02-25", "Completed", "North", "Electronics", 1, "450", "0",  "0"),   # 450
]

results = []


def check(name, actual, expected):
    ok = actual == expected
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {name} | expected {expected}, got {actual}")


data = load_with(SAMPLE)
k = kpi.get_kpis(data)
check("Gross sales", k["gross_sales"], 1260.0)
check("Net sales (after discount and return)", k["net_sales"], 750.0)
check("Order count (cancelled excluded)", k["order_count"], 4)
check("Average order value", k["average_order_value"], 187.5)

month = kpi.revenue_by(data, "month")
check("January net revenue", float(month["2026-01"]), 300.0)
check("February net revenue", float(month["2026-02"]), 450.0)
check("February growth %", float(kpi.growth_by_month(data)["2026-02"]), 50.0)

cat = kpi.revenue_by(data, "category")
check("Electronics revenue", float(cat["Electronics"]), 640.0)
check("Home revenue (returned order nets to 0)", float(cat["Home"]), 0.0)

region = kpi.revenue_by(data, "region")
check("North revenue", float(region["North"]), 690.0)
check("East missing (its only order was cancelled)", "East" in region.index, False)

# ---------- edge cases ----------
empty = load_with([])
check("Empty database: KPIs are zero", kpi.get_kpis(empty),
      {"gross_sales": 0.0, "net_sales": 0.0, "order_count": 0, "average_order_value": 0.0})
check("Empty database: no monthly revenue", len(kpi.revenue_by(empty, "month")), 0)

only_cancelled = load_with([row(1, "2026-03-01", "Cancelled", "East", "Home", 1, "10", "0", "0")])
check("Only cancelled orders: order count is 0", kpi.get_kpis(only_cancelled)["order_count"], 0)

zero_prev = load_with([
    row(1, "2026-01-05", "Returned", "East", "Home", 1, "100", "0", "100"),   # Jan net = 0
    row(2, "2026-02-05", "Completed", "East", "Home", 1, "100", "0", "0"),    # Feb net = 100
])
check("Growth after a zero month does not crash (blank)",
      str(kpi.growth_by_month(zero_prev)["2026-02"]), "nan")

print(f"\n{sum(results)} of {len(results)} KPI tests passed")