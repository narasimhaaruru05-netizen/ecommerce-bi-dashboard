import os
import matplotlib
matplotlib.use("Agg")  # draw straight to image files, no window needed
import matplotlib.pyplot as plt
import kpi

CHART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(CHART_DIR, exist_ok=True)

CHART_NAMES = ["monthly_revenue", "revenue_by_category",
               "revenue_by_region", "growth_by_month"]


def chart_path(name):
    return os.path.join(CHART_DIR, name + ".png")


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(chart_path(name), dpi=120)
    plt.close(fig)


def _no_data(name, title):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.set_title(title)
    ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
    ax.axis("off")
    _save(fig, name)


def monthly_revenue_chart(df):
    title = "Monthly Net Revenue"
    data = kpi.revenue_by(df, "month").sort_index()
    if data.empty:
        return _no_data("monthly_revenue", title)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(data.index, data.values, marker="o", color="#1F4E78", linewidth=2)
    for x, y in zip(data.index, data.values):
        ax.annotate(f"{y:,.0f}", (x, y), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9)
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Net revenue (Rs.)")
    ax.grid(alpha=0.3)
    ax.margins(y=0.12)
    _save(fig, "monthly_revenue")


def _bar_chart(df, column, name, title, xlabel, color):
    data = kpi.revenue_by(df, column).sort_values(ascending=False)
    if data.empty:
        return _no_data(name, title)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(data.index, data.values, color=color)
    ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Net revenue (Rs.)")
    ax.grid(axis="y", alpha=0.3)
    ax.margins(y=0.12)
    _save(fig, name)


def category_chart(df):
    _bar_chart(df, "category", "revenue_by_category",
               "Net Revenue by Product Category", "Category", "#C55A11")


def region_chart(df):
    _bar_chart(df, "region", "revenue_by_region",
               "Net Revenue by Region", "Region", "#2E75B6")


def growth_chart(df):
    title = "Month-over-Month Revenue Growth"
    growth = kpi.growth_by_month(df).dropna()
    if growth.empty:
        return _no_data("growth_by_month", title)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#548235" if v >= 0 else "#C00000" for v in growth.values]
    bars = ax.bar(growth.index, growth.values, color=colors)
    ax.bar_label(bars, fmt="%.2f%%", padding=3, fontsize=9)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Growth vs previous month (%)")
    ax.grid(axis="y", alpha=0.3)
    ax.margins(y=0.12)
    _save(fig, "growth_by_month")


def make_all_charts(df):
    monthly_revenue_chart(df)
    category_chart(df)
    region_chart(df)
    growth_chart(df)
    return CHART_NAMES


if __name__ == "__main__":
    data = kpi.load_data()
    make_all_charts(data)
    for n in CHART_NAMES:
        print("Saved:", chart_path(n))