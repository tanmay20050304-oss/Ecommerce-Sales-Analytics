# 🛒 E-Commerce Sales & Customer Analytics

A full-stack **E-Commerce Sales & Customer Analytics System** built using **Python, Flask, MySQL, HTML, CSS, JavaScript, and Machine Learning**.

The system allows administrators to manage customers, products, and orders while providing SQL-based business analytics and machine-learning features such as **customer churn prediction, sales forecasting, and product recommendations**.

---

## 📌 Project Overview

E-commerce businesses generate large amounts of customer, product, order, payment, and review data.

This project provides a centralized web application to:

* Manage e-commerce data
* Track sales and orders
* Analyze customer purchasing behavior
* Identify high-value customers
* Analyze product performance
* Monitor inventory
* Analyze payment methods
* Predict customer churn
* Forecast future sales
* Generate product recommendations

The project combines **relational database management, SQL analytics, web development, data analysis, and machine learning** in one application.

---

## 🎯 Objectives

The main objectives of this project are:

1. Build a centralized e-commerce management system.
2. Store and manage business data using MySQL.
3. Perform advanced SQL queries for business analytics.
4. Develop an interactive web dashboard using Flask.
5. Analyze customer purchasing behavior using Python.
6. Predict customers who may stop purchasing.
7. Forecast future sales.
8. Recommend products based on customer purchase behavior.
9. Provide an easy-to-use interface for administrators.

---

## ✨ Key Features

### 🔐 Admin Authentication

* Admin login
* Session-based authentication
* Logout functionality
* Protected dashboard pages

### 👥 Customer Management

* Add customers
* View customers
* Update customer information
* Delete customers
* Analyze customer purchasing behavior

### 📦 Product Management

* Add products
* View products
* Update products
* Delete products
* Product category management
* Stock monitoring
* Product rating analysis

### 🛍️ Order Management

* View orders
* Track order information
* Manage order items
* View payment information
* View shipping information

### 📊 Sales Analytics

The system provides SQL-based analytics including:

* Total revenue
* Total orders
* Total customers
* Total products
* Average order value
* Monthly revenue
* Category-wise revenue
* City-wise revenue
* Top customers
* Top products
* Repeat customers
* Payment-method analysis
* Low-stock products

### 🤖 Machine Learning

#### Customer Churn Prediction

Predicts customers who may be likely to stop purchasing based on customer-level purchasing features.

Example features:

* Total orders
* Total spending
* Average order value

#### 📈 Sales Forecasting

Uses historical sales data to estimate future sales trends.

#### 🛒 Product Recommendation

Generates product recommendations based on customer purchase/category behavior.

---

# 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │       User          │
                    │     Web Browser     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Flask App      │
                    │      app.py         │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │   MySQL    │   │   Python   │   │ JavaScript │
       │  Database  │   │ ML / Data  │   │  Charts/UI │
       └────────────┘   └─────┬──────┘   └────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
                  Churn    Forecast  Recommendation
                  Model      Model       System
```

---

# 🗂️ Project Structure

```text
Ecommerce-Sales-Analytics/
│
├── app.py
├── requirements.txt
├── render.yaml
├── README.md
│
├── database/
│   ├── database.sql
│   ├── tables.sql
│   ├── data.sql
│   └── analytics.sql
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── customers.html
│   ├── products.html
│   ├── orders.html
│   ├── analytics.html
│   └── predictions.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── dashboard.js
│
├── python/
│   ├── analysis.py
│   ├── customer_churn.py
│   ├── sales_forecast.py
│   └── recommendation.py
│
└── models/
    ├── churn_model.pkl
    └── forecast_model.pkl
```

---

# 🗄️ Database Design

The application uses **MySQL** as the relational database.

### Main Tables

| Table         | Purpose                            |
| ------------- | ---------------------------------- |
| `admins`      | Stores administrator accounts      |
| `customers`   | Stores customer information        |
| `categories`  | Stores product categories          |
| `products`    | Stores product information         |
| `orders`      | Stores order information           |
| `order_items` | Stores products included in orders |
| `payments`    | Stores payment information         |
| `shipping`    | Stores shipping information        |
| `reviews`     | Stores customer product reviews    |

### Database Relationship

```text
Customers
    │
    │
    ▼
  Orders ─────────── Payments
    │
    │
    ▼
Order Items
    │
    ▼
Products
    │
    ├──────── Categories
    │
    └──────── Reviews

Orders
   │
   ▼
Shipping
```

---

# 💻 Technology Stack

## Frontend

* HTML5
* CSS3
* JavaScript
* Chart.js

## Backend

* Python
* Flask

## Database

* MySQL

## Data Analysis

* Pandas
* NumPy

## Machine Learning

* Scikit-learn
* Random Forest
* Linear Regression

## Model Storage

* Joblib

## Deployment

* GitHub
* Render
* Cloud MySQL

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Ecommerce-Sales-Analytics.git
```

Move into the project:

```bash
cd Ecommerce-Sales-Analytics
```

---

## 2. Create Virtual Environment

### Windows

```powershell
python -m venv venv
```

Activate:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🗄️ MySQL Setup

Make sure MySQL Server and MySQL Workbench are installed.

Create the database by running:

```sql
SOURCE database/database.sql;
```

Then create the tables:

```sql
SOURCE database/tables.sql;
```

Insert sample data:

```sql
SOURCE database/data.sql;
```

Finally execute the analytics queries:

```sql
SOURCE database/analytics.sql;
```

Alternatively, open each `.sql` file in MySQL Workbench and execute it.

---

# 🔑 Database Configuration

For local development, configure your database connection using environment variables.

Create a `.env` file:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=ecommerce_analytics
SECRET_KEY=your_secret_key
```

### ⚠️ Important

Never upload `.env` to GitHub.

Add it to `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
```

---

# ▶️ Run the Application

Start Flask:

```bash
python app.py
```

You should see something similar to:

```text
Running on http://127.0.0.1:5000
```

Open your browser:

```text
http://127.0.0.1:5000
```

---

# 🔐 Demo Login

For the sample database:

```text
Username: admin
Password: admin123
```

> For a production deployment, change the default credentials and use secure password hashing.

---

# 📊 Analytics Modules

## 1. Sales Analytics

The application calculates:

```text
Total Revenue
Total Orders
Average Order Value
Monthly Revenue
Category Revenue
City Revenue
```

Example:

```text
Revenue = SUM(order total amounts)

Average Order Value =
Total Revenue / Total Orders
```

---

## 2. Customer Analytics

The system analyzes:

```text
Customer
   ↓
Number of Orders
   ↓
Total Spending
   ↓
Average Order Value
```

This helps identify customer purchasing patterns.

---

## 3. Product Analytics

Product performance is analyzed using:

* Quantity sold
* Revenue generated
* Product rating
* Category
* Available stock

---

# 🤖 Machine Learning

## Customer Churn Prediction

The churn module uses customer-level features such as:

```text
total_orders
total_spending
average_order_value
```

The model predicts whether a customer belongs to a potential churn group.

The current implementation is a **prototype** where the training target is generated from purchasing rules.

For a production-level system, churn should be defined using a future inactivity period, for example:

```text
Customer purchases
       ↓
Observation period
       ↓
90-day future window
       ↓
No purchase?
       ↓
Churn = 1
```

This provides a more meaningful supervised-learning target.

---

## 📈 Sales Forecasting

Historical monthly revenue is converted into a time-series-like dataset.

Example:

```text
Month 1 → ₹50,000
Month 2 → ₹55,000
Month 3 → ₹61,000
Month 4 → ₹65,000
```

A regression model is then used to estimate future revenue.

---

## 🛒 Product Recommendation

The recommendation module analyzes customer purchasing behavior and product categories.

Example:

```text
Customer purchased:

Laptop
Mouse
Keyboard

        ↓

System analyzes category behavior

        ↓

Recommended:

Laptop Bag
Webcam
USB Hub
```

---

# 📁 Important Python Files

### `analysis.py`

Performs customer and sales analysis using Pandas and MySQL.

### `customer_churn.py`

Trains and saves the customer churn model.

```text
models/churn_model.pkl
```

### `sales_forecast.py`

Trains the sales forecasting model.

```text
models/forecast_model.pkl
```

### `recommendation.py`

Generates product recommendations based on customer purchase behavior.

---

# 📈 Dashboard

The dashboard provides an overview of important business metrics:

```text
┌──────────────────────────────────────────┐
│       E-COMMERCE ANALYTICS DASHBOARD     │
├────────────┬────────────┬────────────────┤
│ Revenue    │ Orders     │ Customers      │
│ ₹XXXX      │ XXXX       │ XXXX           │
├────────────┴────────────┴────────────────┤
│                                          │
│          Monthly Sales Chart             │
│                                          │
├──────────────────────────────────────────┤
│ Top Products │ Top Customers             │
└──────────────────────────────────────────┘
```

---

# 🚀 Deployment

The application can be deployed using:

```text
GitHub
   ↓
Render
   ↓
Flask Application
   ↓
Cloud MySQL
```

### Production Start Command

```bash
gunicorn app:app
```

### Render Build Command

```bash
pip install -r requirements.txt
```

Environment variables required:

```text
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
SECRET_KEY
```

---

# 🔒 Security Considerations

For a production deployment, the following improvements should be implemented:

* Password hashing using Werkzeug or bcrypt
* Secure session configuration
* Environment variables for credentials
* Input validation
* SQL injection protection
* CSRF protection
* HTTPS
* Secure cookies
* Removal of default admin credentials
* Proper authentication and authorization

---

# 🧪 Testing

The project can be tested using:

### Database Testing

* Verify database connection
* Verify foreign-key relationships
* Test CRUD operations
* Test analytical SQL queries

### Backend Testing

* Login
* Logout
* Customer operations
* Product operations
* Order operations
* Analytics routes

### ML Testing

* Model accuracy
* Prediction output
* Forecast results
* Recommendation results

---

# 🔮 Future Enhancements

The project can be extended with:

* Real-time sales analytics
* Advanced customer segmentation
* RFM analysis
* K-Means customer clustering
* Improved time-series forecasting
* XGBoost/Random Forest churn prediction
* Collaborative filtering recommendations
* Email notifications
* Inventory alerts
* REST API
* Role-based authentication
* Admin and employee accounts
* Docker deployment
* Automated model retraining
* Cloud database
* Mobile-responsive dashboard

---

# 🎓 Academic Value

This project demonstrates practical knowledge of:

```text
Database Management
        +
SQL
        +
Python
        +
Flask
        +
Data Analysis
        +
Machine Learning
        +
Web Development
        +
Deployment
```

It can be used as a **final-year academic project** demonstrating the integration of database systems, web technologies, analytics, and machine learning.

---

# 📚 Learning Outcomes

After completing this project, the developer gains practical experience in:

* Designing relational databases
* Writing SQL queries
* Using primary and foreign keys
* Performing joins and aggregations
* Building Flask applications
* Connecting Python with MySQL
* Performing data analysis with Pandas
* Training machine-learning models
* Saving and loading ML models
* Creating interactive dashboards
* Deploying Python applications
* Working with Git and GitHub

---

# 👨‍💻 Author

**Tanmay Paul**

Computer Science / Artificial Intelligence Student

### Areas of Interest

* Artificial Intelligence
* Machine Learning
* Data Analytics
* Python
* SQL
* Full-Stack Development

---

# ⭐ Project Highlights

```text
✓ MySQL Database
✓ SQL Analytics
✓ Flask Web Application
✓ Customer Management
✓ Product Management
✓ Order Management
✓ Sales Dashboard
✓ Customer Analytics
✓ Churn Prediction
✓ Sales Forecasting
✓ Product Recommendation
✓ Machine Learning
✓ GitHub Ready
✓ Cloud Deployment Ready
```

---

# 📄 License

This project is developed for **educational and academic purposes**.

You may modify and extend the project for learning and academic use.

