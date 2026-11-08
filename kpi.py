import numpy as np
import pandas as pd
from db import get_connection

COLUMNS = ["order_id", "order_date", "order_status", "region",
           "category", "quantity", "unit_price", "discount", "return_amount"]


def load_data():
    """Read all order lines from MySQL and return a clean Pandas table."""
    query = """
        SELECT o.order_id, o.order_date, o.order_status, o.region,
               p.category, i.quantity, i.unit_price, i.discount, i.return_amount
        FROM order_items i
        JOIN orders o ON i.order_id = o.order_id
        JOIN products p ON i.product_id = p.product_id
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=COLUMNS)

    # MySQL DECIMAL values arrive as Decimal; convert to normal numbers
    for col in ["quantity", "unit_price", "discount", "return_amount"]:
        df[col] = df[col].astype(float)

    # Rule: cancelled orders are excluded from every KPI
    df = df[df["order_status"] != "Cancelled"].copy()

    # Formulas
    df["gross"] = df["quantity"] * df["unit_price"]
    df["net"] = df["gross"] - df["discount"] - df["return_amount"]
    df["month"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m")
    return df


def get_kpis(df):
    """The four headline numbers."""
    order_count = int(df["order_id"].nunique())
    gross = float(df["gross"].sum())
    net = float(df["net"].sum())
    aov = net / order_count if order_count > 0 else 0.0
    return {
        "gross_sales": round(gross, 2),
        "net_sales": round(net, 2),
        "order_count": order_count,
        "average_order_value": round(aov, 2),
    }


def revenue_by(df, column):
    """Net sales grouped by 'month', 'category' or 'region'."""
    return df.groupby(column)["net"].sum().round(2)


def growth_by_month(df):
    """Month-over-month growth in percent, calculated with NumPy."""
    monthly = revenue_by(df, "month").sort_index()
    values = monthly.to_numpy(dtype=float)

    growth = np.full(len(values), np.nan)          # first month has no previous month
    if len(values) > 1:
        previous = values[:-1]
        current = values[1:]
        safe_previous = np.where(previous != 0, previous, 1)   # avoid dividing by zero
        change = (current - previous) / safe_previous * 100
        growth[1:] = np.where(previous != 0, change, np.nan)   # blank when previous is 0

    return pd.Series(np.round(growth, 2), index=monthly.index)


if __name__ == "__main__":
    data = load_data()
    print("KPIs:", get_kpis(data))
    print("\nRevenue by month:\n", revenue_by(data, "month"))
    print("\nRevenue by category:\n", revenue_by(data, "category"))
    print("\nRevenue by region:\n", revenue_by(data, "region"))
    print("\nGrowth % by month:\n", growth_by_month(data))