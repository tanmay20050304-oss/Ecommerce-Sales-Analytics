import mysql.connector
import pandas as pd


def get_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_PASSWORD",
        database="ecommerce_analytics"
    )


connection = get_connection()


query = """
SELECT
    c.customer_name,
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spending,
    AVG(o.total_amount) AS average_order_value

FROM customers c

JOIN orders o
ON c.customer_id = o.customer_id

WHERE o.order_status <> 'Cancelled'

GROUP BY
    c.customer_id,
    c.customer_name,
    c.city

ORDER BY total_spending DESC
"""


df = pd.read_sql(query, connection)

print("\nCUSTOMER ANALYSIS")
print(df)


print("\nTOP CUSTOMER")

print(df.iloc[0])


print("\nSTATISTICS")

print(df["total_spending"].describe())


connection.close()