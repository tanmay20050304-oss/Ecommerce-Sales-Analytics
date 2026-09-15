import os
from pathlib import Path

try:
    import mysql.connector
except ImportError:  # pragma: no cover
    mysql = None


DB_PATH = Path(__file__).resolve().parent.parent / "database" / "ecommerce_analytics.db"


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

    import sqlite3
    connection = sqlite3.connect(str(DB_PATH))
    return connection


connection = get_connection()
customer_id = 1

query = """
SELECT DISTINCT
    p2.product_name
FROM orders o1
JOIN order_items oi1
    ON o1.order_id = oi1.order_id
JOIN orders o2
    ON o1.customer_id = o2.customer_id
JOIN order_items oi2
    ON o2.order_id = oi2.order_id
JOIN products p1
    ON oi1.product_id = p1.product_id
JOIN products p2
    ON oi2.product_id = p2.product_id
WHERE o1.customer_id = ?
  AND p1.category_id = p2.category_id
  AND p1.product_id <> p2.product_id
LIMIT 5
"""

cursor = connection.cursor()
cursor.execute(query, (customer_id,))
recommendations = cursor.fetchall()

print("Recommended Products:")
for product in recommendations:
    print(product[0])

cursor.close()
connection.close()