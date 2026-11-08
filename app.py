from datetime import datetime
from flask import Flask, jsonify, request, send_file
import mysql.connector
import pandas as pd
from db import get_connection
import kpi
import charts

app = Flask(__name__)
VALID_STATUS = {"Completed", "Cancelled", "Returned"}


# ---------- helpers ----------
def run_query(sql, params=(), fetch=False, one=False):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        if fetch:
            return cur.fetchone() if one else cur.fetchall()
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def error(msg, code=400):
    return jsonify({"error": msg}), code


def non_negative_number(value):
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


# ---------- error handlers ----------
@app.errorhandler(mysql.connector.Error)
def handle_db_error(e):
    if e.errno == 1451:
        return error("Cannot delete: this record is used by other records", 409)
    if e.errno == 1452:
        return error("Invalid reference: related product/order does not exist", 400)
    return error("Database error: " + str(e), 500)


@app.errorhandler(404)
def not_found(e):
    return error("Route not found", 404)


# ---------- home and health check ----------
@app.route("/")
def home():
    return jsonify({
        "project": "E-Commerce Business Intelligence Dashboard",
        "endpoints": ["/health", "/products", "/orders", "/order-items",
                      "/kpis", "/revenue/month", "/revenue/category",
                      "/revenue/region", "/growth",
                      "/charts/monthly_revenue", "/charts/revenue_by_category",
                      "/charts/revenue_by_region", "/charts/growth_by_month"]
    })


@app.route("/health")
def health():
    try:
        get_connection().close()
        return jsonify({"status": "ok", "database": "connected"})
    except mysql.connector.Error as e:
        return jsonify({"status": "error", "database": str(e)}), 500


# ---------- products ----------
@app.route("/products", methods=["GET"])
def list_products():
    return jsonify(run_query("SELECT * FROM products", fetch=True))


@app.route("/products/<int:pid>", methods=["GET"])
def get_product(pid):
    p = run_query("SELECT * FROM products WHERE product_id=%s", (pid,), fetch=True, one=True)
    return jsonify(p) if p else error("Product not found", 404)


@app.route("/products", methods=["POST"])
def add_product():
    d = request.get_json(silent=True) or {}
    name = str(d.get("product_name", "")).strip()
    cat = str(d.get("category", "")).strip()
    if not name or not cat:
        return error("product_name and category are required")
    pid = run_query("INSERT INTO products (product_name, category) VALUES (%s,%s)", (name, cat))
    return jsonify({"message": "Product added", "product_id": pid}), 201


@app.route("/products/<int:pid>", methods=["PUT"])
def update_product(pid):
    if not run_query("SELECT 1 FROM products WHERE product_id=%s", (pid,), fetch=True, one=True):
        return error("Product not found", 404)
    d = request.get_json(silent=True) or {}
    name = str(d.get("product_name", "")).strip()
    cat = str(d.get("category", "")).strip()
    if not name or not cat:
        return error("product_name and category are required")
    run_query("UPDATE products SET product_name=%s, category=%s WHERE product_id=%s", (name, cat, pid))
    return jsonify({"message": "Product updated"})


@app.route("/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    if not run_query("SELECT 1 FROM products WHERE product_id=%s", (pid,), fetch=True, one=True):
        return error("Product not found", 404)
    run_query("DELETE FROM products WHERE product_id=%s", (pid,))
    return jsonify({"message": "Product deleted"})


# ---------- orders ----------
@app.route("/orders", methods=["GET"])
def list_orders():
    status = request.args.get("status")
    if status:
        if status not in VALID_STATUS:
            return error("status must be Completed, Cancelled or Returned")
        rows = run_query("SELECT * FROM orders WHERE order_status=%s", (status,), fetch=True)
    else:
        rows = run_query("SELECT * FROM orders", fetch=True)
    return jsonify(rows)


@app.route("/orders/<int:oid>", methods=["GET"])
def get_order(oid):
    o = run_query("SELECT * FROM orders WHERE order_id=%s", (oid,), fetch=True, one=True)
    if not o:
        return error("Order not found", 404)
    o["items"] = run_query("SELECT * FROM order_items WHERE order_id=%s", (oid,), fetch=True)
    return jsonify(o)


@app.route("/orders", methods=["POST"])
def add_order():
    d = request.get_json(silent=True) or {}
    try:
        datetime.strptime(str(d.get("order_date", "")), "%Y-%m-%d")
    except ValueError:
        return error("order_date must be in YYYY-MM-DD format")
    if d.get("order_status") not in VALID_STATUS:
        return error("order_status must be Completed, Cancelled or Returned")
    region = str(d.get("region", "")).strip()
    if not region:
        return error("region is required")
    oid = run_query(
        "INSERT INTO orders (order_date, order_status, region) VALUES (%s,%s,%s)",
        (d["order_date"], d["order_status"], region))
    return jsonify({"message": "Order added", "order_id": oid}), 201


@app.route("/orders/<int:oid>", methods=["PUT"])
def update_order_status(oid):
    if not run_query("SELECT 1 FROM orders WHERE order_id=%s", (oid,), fetch=True, one=True):
        return error("Order not found", 404)
    d = request.get_json(silent=True) or {}
    if d.get("order_status") not in VALID_STATUS:
        return error("order_status must be Completed, Cancelled or Returned")
    run_query("UPDATE orders SET order_status=%s WHERE order_id=%s", (d["order_status"], oid))
    return jsonify({"message": "Order status updated"})


@app.route("/orders/<int:oid>", methods=["DELETE"])
def delete_order(oid):
    if not run_query("SELECT 1 FROM orders WHERE order_id=%s", (oid,), fetch=True, one=True):
        return error("Order not found", 404)
    run_query("DELETE FROM order_items WHERE order_id=%s", (oid,))
    run_query("DELETE FROM orders WHERE order_id=%s", (oid,))
    return jsonify({"message": "Order and its items deleted"})


# ---------- order items ----------
@app.route("/order-items", methods=["POST"])
def add_order_item():
    d = request.get_json(silent=True) or {}
    try:
        order_id = int(d["order_id"])
        product_id = int(d["product_id"])
        qty = int(d["quantity"])
    except (KeyError, TypeError, ValueError):
        return error("order_id, product_id and quantity must be integers")
    if qty <= 0:
        return error("quantity must be greater than 0")
    price = d.get("unit_price")
    discount = d.get("discount", 0)
    ret = d.get("return_amount", 0)
    for label, val in (("unit_price", price), ("discount", discount), ("return_amount", ret)):
        if not non_negative_number(val):
            return error(label + " must be a number >= 0")
    iid = run_query(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount, return_amount) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (order_id, product_id, qty, price, discount, ret))
    return jsonify({"message": "Order item added", "item_id": iid}), 201


# ---------- KPI routes ----------
@app.route("/kpis", methods=["GET"])
def kpis():
    data = kpi.load_data()
    return jsonify(kpi.get_kpis(data))


@app.route("/revenue/<by>", methods=["GET"])
def revenue(by):
    if by not in ("month", "category", "region"):
        return error("by must be month, category or region")
    data = kpi.load_data()
    return jsonify(kpi.revenue_by(data, by).to_dict())


@app.route("/growth", methods=["GET"])
def growth():
    data = kpi.load_data()
    g = kpi.growth_by_month(data)
    return jsonify({m: (None if pd.isna(v) else v) for m, v in g.to_dict().items()})


# ---------- chart routes ----------
@app.route("/charts/<name>", methods=["GET"])
def chart(name):
    if name not in charts.CHART_NAMES:
        return error("Unknown chart. Use: " + ", ".join(charts.CHART_NAMES), 404)
    data = kpi.load_data()
    charts.make_all_charts(data)
    return send_file(charts.chart_path(name), mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)