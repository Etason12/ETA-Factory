# ARCHITECTURE.md

## System Architecture

Frontend (React + Vite)

↓

REST API

↓

Flask Backend

↓

PostgreSQL Database

---

# Backend Structure

backend/

src/

api/

auth/

users/

branches/

products/

inventory/

warehouses/

production/

sales/

transfers/

reports/

audit/

services/

repositories/

models/

schemas/

utils/

config/

---

# Frontend Structure

frontend/

src/

api/

pages/

components/

layouts/

hooks/

contexts/

store/

routes/

types/

utils/

assets/

---

# Main Modules

1. Authentication

* Login
* Logout
* Refresh Token
* Change Password

2. User Management

* Users
* Roles
* Permissions

3. Branch Management

* Branches
* Stores
* Warehouses

4. Product Management

* Products
* Categories
* Units

5. Production

* Production Orders
* Finished Goods
* Production Batches

6. Inventory

* Stock Ledger
* Inventory Movements

7. Warehouse

* GRV
* GIV
* Transfers

8. Sales

* Quotations
* Orders
* Invoices
* Payments

9. Customers

* Customer Accounts
* Customer History

10. Reporting

* Sales Reports
* Inventory Reports
* Transfer Reports
* Production Reports

11. Audit

* Activity Logs
* Approval Logs

---

# Multi-Branch Rules

Every transaction belongs to a branch.

Users can only access authorized branches.

Owner can access all branches.

Branch Managers access assigned branches only.

---

# API Design

Use:

/api/v1/

Examples:

/api/v1/auth/login

/api/v1/products

/api/v1/customers

/api/v1/sales-orders

/api/v1/transfers

/api/v1/reports

Use JSON responses only.

Use pagination for large datasets.
