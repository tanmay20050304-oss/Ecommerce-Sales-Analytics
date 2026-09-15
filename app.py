from flask import Flask, render_template, request, redirect, session, url_for
import os
from pathlib import Path
import sqlite3
import joblib
import subprocess
import sys
import pandas as pd

try:
    import mysql.connector
except ImportError:  # pragma: no cover - optional dependency for MySQL deployments
    mysql = None

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ecommerce_secret_key")

DB_PATH = Path(__file__).resolve().parent / "database" / "ecommerce_analytics.db"
MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def ensure_models_exist():
    churn_model = MODEL_DIR / "churn_model.pkl"
    forecast_model = MODEL_DIR / "forecast_model.pkl"

    if churn_model.exists() and forecast_model.exists():
        return

    scripts = [
        Path(__file__).resolve().parent / "python" / "customer_churn.py",
        Path(__file__).resolve().parent / "python" / "sales_forecast.py",
    ]

    for script in scripts:
        if script.exists():
            subprocess.run([sys.executable, str(script)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_customer_churn_risk():
    ensure_models_exist()

    churn_model = joblib.load(MODEL_DIR / "churn_model.pkl")
    connection = sqlite_connect()
    rows = connection.execute(
        """
        SELECT
            c.customer_id,
            c.customer_name,
            COUNT(o.order_id) AS total_orders,
            COALESCE(SUM(o.total_amount), 0) AS total_spending,
            COALESCE(AVG(o.total_amount), 0) AS average_order_value
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.customer_name
        ORDER BY total_spending DESC
        """
    ).fetchall()
    connection.close()

    risk_rows = []
    max_spending = max((float(row["total_spending"]) for row in rows), default=1.0)
    for row in rows:
        features = pd.DataFrame(
            [[row["total_orders"], row["total_spending"], row["average_order_value"]]],
            columns=["total_orders", "total_spending", "average_order_value"],
        )
        if hasattr(churn_model, "classes_") and len(churn_model.classes_) > 1:
            try:
                prob = float(churn_model.predict_proba(features)[0][1])
            except IndexError:
                prob = float(churn_model.predict(features)[0])
        else:
            prob = max(0.0, min(1.0, 1.0 - (float(row["total_spending"]) / max_spending)))

        risk_rows.append({
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"],
            "total_orders": row["total_orders"],
            "total_spending": float(row["total_spending"]),
            "average_order_value": float(row["average_order_value"]),
            "risk_score": round(prob * 100, 1),
        })

    return sorted(risk_rows, key=lambda item: item["risk_score"], reverse=True)[:5]


def get_sales_forecast():
    ensure_models_exist()

    forecast_model = joblib.load(MODEL_DIR / "forecast_model.pkl")
    connection = sqlite_connect()
    month_rows = connection.execute(
        """
        SELECT strftime('%Y-%m', order_date) AS month, SUM(total_amount) AS revenue
        FROM orders
        WHERE order_status <> 'Cancelled'
        GROUP BY month
        ORDER BY month
        """
    ).fetchall()
    connection.close()

    next_month_number = len(month_rows) + 1
    future_df = pd.DataFrame([[next_month_number]], columns=["month_number"])
    prediction = float(forecast_model.predict(future_df)[0])

    return {
        "next_month_number": next_month_number,
        "predicted_revenue": round(prediction, 2),
        "previous_months": [
            {"month": row["month"], "revenue": float(row["revenue"])} for row in month_rows
        ],
    }


def get_recommendations():
    connection = sqlite_connect()
    top_customer = connection.execute(
        """
        SELECT c.customer_id, c.customer_name
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.customer_name
        ORDER BY COALESCE(SUM(o.total_amount), 0) DESC
        LIMIT 1
        """
    ).fetchone()

    if top_customer is None:
        connection.close()
        return []

    rows = connection.execute(
        """
                SELECT DISTINCT p2.product_name, p2.price, c.category_name
        FROM orders o1
        JOIN order_items oi1 ON o1.order_id = oi1.order_id
        JOIN products p1 ON oi1.product_id = p1.product_id
        JOIN products p2 ON p1.category_id = p2.category_id
        JOIN categories c ON p2.category_id = c.category_id
        WHERE o1.customer_id = ?
                    AND p1.category_id = p2.category_id
          AND p2.product_id <> p1.product_id
        GROUP BY p2.product_id, p2.product_name, p2.price, c.category_name
        ORDER BY p2.rating DESC, p2.price DESC
        LIMIT 5
        """,
        (top_customer["customer_id"],),
    ).fetchall()
    connection.close()

    recommendations = []
    for row in rows:
        recommendations.append({
            "product_name": row["product_name"],
            "price": float(row["price"]),
            "category_name": row["category_name"],
        })

    if not recommendations:
        connection = sqlite_connect()
        fallback = connection.execute(
            "SELECT product_name, price, category_name FROM products p JOIN categories c ON p.category_id = c.category_id ORDER BY rating DESC LIMIT 5"
        ).fetchall()
        connection.close()
        recommendations = [
            {"product_name": item["product_name"], "price": float(item["price"]), "category_name": item["category_name"]}
            for item in fallback
        ]

    return recommendations


def sqlite_connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def get_cursor(connection):
    if isinstance(connection, sqlite3.Connection):
        return connection.cursor()
    return connection.cursor(dictionary=True)


def get_connection():
    use_sqlite = os.getenv("USE_SQLITE", "1").lower() in {"1", "true", "yes", "on"}
    if mysql is not None and not use_sqlite:
        try:
            return mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "localhost"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", ""),
                database=os.getenv("MYSQL_DATABASE", "ecommerce_analytics"),
                port=int(os.getenv("MYSQL_PORT", "3306")),
                autocommit=True,
            )
        except Exception:
            pass
    return sqlite_connect()


def seed_sqlite_data():
    connection = sqlite_connect()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'India',
            registration_date TEXT,
            gender TEXT,
            age INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category_id INTEGER,
            price REAL,
            stock_quantity INTEGER,
            brand TEXT,
            rating REAL,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            order_status TEXT,
            total_amount REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            payment_date TEXT,
            payment_method TEXT,
            payment_status TEXT,
            amount REAL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipping (
            shipping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            shipping_date TEXT,
            delivery_date TEXT,
            shipping_status TEXT,
            shipping_city TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER,
            review_text TEXT,
            review_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    cursor.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)", ("admin", "admin123"))

    categories = [
        ("Electronics", "Electronic devices and accessories"),
        ("Clothing", "Men and women clothing"),
        ("Home Appliances", "Appliances for home"),
        ("Books", "Educational and general books"),
        ("Sports", "Sports equipment and accessories"),
        ("Beauty", "Beauty and personal care products"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO categories (category_name, description) VALUES (?, ?)",
        categories,
    )

    products = [
        ("Laptop", 1, 65000, 25, "Dell", 4.5),
        ("Smartphone", 1, 30000, 40, "Samsung", 4.4),
        ("Wireless Mouse", 1, 1200, 100, "Logitech", 4.3),
        ("Keyboard", 1, 1800, 80, "HP", 4.2),
        ("T-Shirt", 2, 800, 150, "Puma", 4.1),
        ("Jeans", 2, 1800, 100, "Levi's", 4.4),
        ("Washing Machine", 3, 32000, 20, "LG", 4.5),
        ("Microwave Oven", 3, 12000, 30, "IFB", 4.2),
        ("Python Programming", 4, 900, 50, "TechPress", 4.6),
        ("Data Science Book", 4, 1200, 45, "OReilly", 4.7),
        ("Cricket Bat", 5, 2500, 35, "SS", 4.3),
        ("Running Shoes", 5, 3500, 60, "Nike", 4.5),
        ("Face Wash", 6, 500, 100, "Nivea", 4.0),
        ("Perfume", 6, 2500, 40, "Park Avenue", 4.2),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO products (product_name, category_id, price, stock_quantity, brand, rating) VALUES (?, ?, ?, ?, ?, ?)",
        products,
    )

    customers = [
        ("Amit Sharma", "amit@gmail.com", "9876543210", "Kolkata", "West Bengal", "India", "2025-01-10", "Male", 24),
        ("Priya Singh", "priya@gmail.com", "9876543211", "Delhi", "Delhi", "India", "2025-01-15", "Female", 27),
        ("Rahul Das", "rahul@gmail.com", "9876543212", "Siliguri", "West Bengal", "India", "2025-02-05", "Male", 22),
        ("Sneha Roy", "sneha@gmail.com", "9876543213", "Mumbai", "Maharashtra", "India", "2025-02-20", "Female", 26),
        ("Arjun Patel", "arjun@gmail.com", "9876543214", "Ahmedabad", "Gujarat", "India", "2025-03-01", "Male", 29),
        ("Ananya Sen", "ananya@gmail.com", "9876543215", "Kolkata", "West Bengal", "India", "2025-03-12", "Female", 23),
        ("Rohan Gupta", "rohan@gmail.com", "9876543216", "Bangalore", "Karnataka", "India", "2025-03-18", "Male", 31),
        ("Neha Verma", "neha@gmail.com", "9876543217", "Pune", "Maharashtra", "India", "2025-04-02", "Female", 25),
        ("Vikash Kumar", "vikash@gmail.com", "9876543218", "Patna", "Bihar", "India", "2025-04-10", "Male", 28),
        ("Pooja Das", "pooja@gmail.com", "9876543219", "Guwahati", "Assam", "India", "2025-04-20", "Female", 24),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO customers (customer_name, email, phone, city, state, country, registration_date, gender, age) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        customers,
    )

    orders = [
        (1, "2025-05-01", "Delivered", 66200),
        (2, "2025-05-03", "Delivered", 30800),
        (3, "2025-05-05", "Delivered", 2500),
        (4, "2025-05-08", "Delivered", 12000),
        (5, "2025-05-10", "Delivered", 3500),
        (6, "2025-05-15", "Shipped", 67000),
        (7, "2025-05-18", "Delivered", 4200),
        (8, "2025-05-20", "Delivered", 30000),
        (9, "2025-05-22", "Pending", 1800),
        (10, "2025-05-25", "Delivered", 900),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO orders (customer_id, order_date, order_status, total_amount) VALUES (?, ?, ?, ?)",
        orders,
    )

    order_items = [
        (1, 1, 1, 65000),
        (1, 3, 1, 1200),
        (2, 2, 1, 30000),
        (2, 4, 1, 1800),
        (3, 11, 1, 2500),
        (4, 8, 1, 12000),
        (5, 12, 1, 3500),
        (6, 1, 1, 65000),
        (6, 3, 1, 1200),
        (6, 4, 1, 1800),
        (7, 5, 1, 800),
        (7, 6, 1, 1800),
        (7, 13, 2, 500),
        (8, 2, 1, 30000),
        (9, 6, 1, 1800),
        (10, 9, 1, 900),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
        order_items,
    )

    payments = [
        (1, "2025-05-01", "UPI", "Paid", 66200),
        (2, "2025-05-03", "Credit Card", "Paid", 30800),
        (3, "2025-05-05", "UPI", "Paid", 2500),
        (4, "2025-05-08", "Debit Card", "Paid", 12000),
        (5, "2025-05-10", "UPI", "Paid", 3500),
        (6, "2025-05-15", "Credit Card", "Paid", 67000),
        (7, "2025-05-18", "UPI", "Paid", 4200),
        (8, "2025-05-20", "Net Banking", "Paid", 30000),
        (9, "2025-05-22", "Cash on Delivery", "Pending", 1800),
        (10, "2025-05-25", "UPI", "Paid", 900),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO payments (order_id, payment_date, payment_method, payment_status, amount) VALUES (?, ?, ?, ?, ?)",
        payments,
    )

    shipping = [
        (1, "2025-05-02", "2025-05-05", "Delivered", "Kolkata"),
        (2, "2025-05-04", "2025-05-07", "Delivered", "Delhi"),
        (3, "2025-05-06", "2025-05-09", "Delivered", "Siliguri"),
        (4, "2025-05-09", "2025-05-13", "Delivered", "Mumbai"),
        (5, "2025-05-11", "2025-05-14", "Delivered", "Ahmedabad"),
        (6, "2025-05-16", None, "In Transit", "Kolkata"),
        (7, "2025-05-19", "2025-05-23", "Delivered", "Bangalore"),
        (8, "2025-05-21", "2025-05-25", "Delivered", "Pune"),
        (9, None, None, "Processing", "Patna"),
        (10, "2025-05-26", "2025-05-29", "Delivered", "Guwahati"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO shipping (order_id, shipping_date, delivery_date, shipping_status, shipping_city) VALUES (?, ?, ?, ?, ?)",
        shipping,
    )

    reviews = [
        (1, 1, 5, "Excellent laptop", "2025-05-06"),
        (1, 3, 4, "Good mouse", "2025-05-06"),
        (2, 2, 5, "Very good phone", "2025-05-08"),
        (3, 11, 4, "Good bat", "2025-05-10"),
        (4, 8, 4, "Works well", "2025-05-14"),
        (5, 12, 5, "Very comfortable shoes", "2025-05-15"),
        (6, 1, 5, "Great performance", "2025-05-20"),
        (7, 5, 4, "Nice quality", "2025-05-24"),
        (8, 2, 4, "Good smartphone", "2025-05-26"),
        (10, 9, 5, "Very useful book", "2025-05-30"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO reviews (customer_id, product_id, rating, review_text, review_date) VALUES (?, ?, ?, ?, ?)",
        reviews,
    )

    connection.commit()
    connection.close()


seed_sqlite_data()


@app.route("/")
def home():
    if "admin" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = get_cursor(connection)

    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) AS revenue
        FROM orders
        WHERE order_status <> 'Cancelled'
    """)
    revenue = cursor.fetchone()["revenue"]

    cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
    orders = cursor.fetchone()["total_orders"]

    cursor.execute("SELECT COUNT(*) AS total_customers FROM customers")
    customers = cursor.fetchone()["total_customers"]

    cursor.execute("SELECT COUNT(*) AS total_products FROM products")
    products = cursor.fetchone()["total_products"]

    cursor.close()
    connection.close()

    return render_template("dashboard.html", revenue=revenue, orders=orders, customers=customers, products=products)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = get_connection()
        cursor = get_cursor(connection)

        cursor.execute("""
            SELECT *
            FROM admins
            WHERE username = ?
            AND password = ?
        """, (username, password))
        admin = cursor.fetchone()

        cursor.close()
        connection.close()

        if admin:
            session["admin"] = admin["username"]
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/customers", methods=["GET", "POST"])
def customers():
    if "admin" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = get_cursor(connection)

    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        email = request.form.get("email", "").strip()

        if not name or not email:
            cursor.close()
            connection.close()
            return redirect(url_for("customers", error="Name and email are required"))

        try:
            cursor.execute(
                """
                INSERT INTO customers
                    (customer_name, email, phone, city, state, country, registration_date, gender, age)
                VALUES (?, ?, ?, ?, ?, ?, date('now'), ?, ?)
                """,
                (
                    name,
                    email,
                    request.form.get("phone", "").strip(),
                    request.form.get("city", "").strip(),
                    request.form.get("state", "").strip(),
                    request.form.get("country", "India").strip() or "India",
                    request.form.get("gender", "").strip(),
                    request.form.get("age") or None,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()

        cursor.close()
        connection.close()
        return redirect(url_for("customers"))

    cursor.execute("SELECT * FROM customers ORDER BY customer_id DESC")
    data = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("customers.html", customers=data)


@app.route("/products", methods=["GET", "POST"])
def products():
    if "admin" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = get_cursor(connection)

    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        category_id = request.form.get("category_id")

        if product_name and category_id:
            cursor.execute(
                """
                INSERT INTO products
                    (product_name, category_id, price, stock_quantity, brand, rating)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_name,
                    category_id,
                    request.form.get("price") or 0,
                    request.form.get("stock_quantity") or 0,
                    request.form.get("brand", "").strip(),
                    request.form.get("rating") or 0,
                ),
            )
            connection.commit()

        cursor.close()
        connection.close()
        return redirect(url_for("products"))

    cursor.execute("""
        SELECT
            p.*, c.category_name
        FROM products p
        LEFT JOIN categories c
            ON p.category_id = c.category_id
        ORDER BY p.product_id DESC
    """)
    data = cursor.fetchall()
    cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("products.html", products=data, categories=categories)


@app.route("/orders", methods=["GET", "POST"])
def orders():
    if "admin" not in session:
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        product_id = request.form.get("product_id")
        quantity = request.form.get("quantity", "0")
        order_status = request.form.get("order_status", "Pending")
        order_date = request.form.get("order_date") or __import__("datetime").date.today().isoformat()

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 0

        if not customer_id or not product_id or quantity <= 0:
            error = "Please select a customer, product, and valid quantity."
        else:
            connection = get_connection()
            cursor = get_cursor(connection)

            cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
            product = cursor.fetchone()

            if not product:
                error = "Selected product was not found."
            else:
                unit_price = float(product["price"])
                total_amount = unit_price * quantity

                cursor.execute(
                    "INSERT INTO orders (customer_id, order_date, order_status, total_amount) VALUES (?, ?, ?, ?)",
                    (customer_id, order_date, order_status, total_amount),
                )
                order_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, product_id, quantity, unit_price),
                )
                connection.commit()

                cursor.close()
                connection.close()
                return redirect(url_for("orders"))

            cursor.close()
            connection.close()

    connection = get_connection()
    cursor = get_cursor(connection)
    cursor.execute("""
        SELECT
            o.order_id,
            c.customer_name,
            o.order_date,
            o.order_status,
            o.total_amount
        FROM orders o
        JOIN customers c
            ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC
    """)
    data = cursor.fetchall()

    cursor.execute("SELECT customer_id, customer_name FROM customers ORDER BY customer_name")
    customers = cursor.fetchall()

    cursor.execute("SELECT product_id, product_name, price FROM products ORDER BY product_name")
    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("orders.html", orders=data, customers=customers, products=products, error=error)


@app.route("/analytics")
def analytics():
    if "admin" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = get_cursor(connection)

    cursor.execute("""
        SELECT
            p.product_name,
            SUM(oi.quantity) AS units_sold,
            SUM(oi.quantity * oi.unit_price) AS revenue
        FROM products p
        JOIN order_items oi
            ON p.product_id = oi.product_id
        JOIN orders o
            ON oi.order_id = o.order_id
        WHERE o.order_status <> 'Cancelled'
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT 10
    """)
    top_products = cursor.fetchall()

    cursor.execute("""
        SELECT
            c.category_name,
            SUM(oi.quantity * oi.unit_price) AS revenue
        FROM categories c
        JOIN products p
            ON c.category_id = p.category_id
        JOIN order_items oi
            ON p.product_id = oi.product_id
        JOIN orders o
            ON oi.order_id = o.order_id
        WHERE o.order_status <> 'Cancelled'
        GROUP BY c.category_id, c.category_name
        ORDER BY revenue DESC
    """)
    categories = cursor.fetchall()

    cursor.execute("""
        SELECT
            strftime('%Y-%m', order_date) AS month,
            SUM(total_amount) AS revenue
        FROM orders
        WHERE order_status <> 'Cancelled'
        GROUP BY month
        ORDER BY month
    """)
    monthly = cursor.fetchall()

    cursor.execute("""
        SELECT
            c.customer_name,
            SUM(o.total_amount) AS spending
        FROM customers c
        JOIN orders o
            ON c.customer_id = o.customer_id
        WHERE o.order_status <> 'Cancelled'
        GROUP BY c.customer_id, c.customer_name
        ORDER BY spending DESC
        LIMIT 10
    """)
    top_customers = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("analytics.html", top_products=top_products, categories=categories, monthly=monthly, top_customers=top_customers)


@app.route("/predictions")
def predictions():
    if "admin" not in session:
        return redirect(url_for("login"))

    churn_risk = get_customer_churn_risk()
    sales_forecast = get_sales_forecast()
    recommendations = get_recommendations()

    return render_template(
        "predictions.html",
        churn_risk=churn_risk,
        sales_forecast=sales_forecast,
        recommendations=recommendations,
    )


if __name__ == "__main__":
    app.run(debug=True)

    