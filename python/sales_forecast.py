import os
from pathlib import Path

import pandas as pd
import joblib

try:
    import mysql.connector
except ImportError:  # pragma: no cover
    mysql = None

from sklearn.linear_model import LinearRegression


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
    strftime('%Y-%m', order_date) AS month,
    SUM(total_amount) AS revenue
FROM orders
WHERE order_status <> 'Cancelled'
GROUP BY month
ORDER BY month
"""


df = pd.read_sql_query(query, connection)

if df.empty:
    raise ValueError("No sales data found. Please add orders before running the forecast model.")


df["month_number"] = range(1, len(df) + 1)
X = df[["month_number"]]
y = df["revenue"]

model = LinearRegression()
model.fit(X, y)

next_month = [[len(df) + 1]]
prediction = model.predict(next_month)

print("Predicted Next Month Revenue:", prediction[0])
joblib.dump(model, str(MODEL_DIR / "forecast_model.pkl"))

connection.close()