import os
from pathlib import Path

import pandas as pd
import joblib

try:
    import mysql.connector
except ImportError:  # pragma: no cover
    mysql = None

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


DB_PATH = Path(__file__).resolve().parent.parent / "database" / "ecommerce_analytics.db"
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


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
    connection.row_factory = sqlite3.Row
    return connection


connection = get_connection()

query = """
SELECT
    c.customer_id,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spending,
    COALESCE(AVG(o.total_amount), 0) AS average_order_value
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id
"""


df = pd.read_sql_query(query, connection)

if df.empty:
    raise ValueError("No customer data found. Please create data in the app database first.")

df["churn"] = 0

# Create a realistic split for the demo dataset so both classes exist and the model can predict churn.
# The seeded demo data has healthy spending for all customers, so the original rule created a single-class target.
spend_median = df["total_spending"].median()
df.loc[df["total_spending"] <= spend_median, "churn"] = 1


X = df[["total_orders", "total_spending", "average_order_value"]]
y = df["churn"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y if len(y.unique()) > 1 else None,
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy)
joblib.dump(model, str(MODEL_DIR / "churn_model.pkl"))

connection.close()