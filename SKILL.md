# SKILL.md

## Project Identity

This project is a multi-branch ETA Factory ERP system built by ETACOM Technology.

The system manages:

* Production
* Warehouses
* Stores
* Sales Outlets
* Customers
* Inventory
* Transfers
* Reporting

Branches include:

* Addis Ababa
* Mekelle
* Future branches

The application must support unlimited branches.

---

# Tech Stack

Frontend:

* React
* Vite
* TypeScript
* Material UI
* React Router
* React Query
* Axios
* Zustand

Backend:

* Python 3.12+
* Flask
* Flask SQLAlchemy
* Flask JWT Extended
* Marshmallow
* Alembic

Database:

* PostgreSQL

Deployment:

* Docker
* Nginx
* Ubuntu Linux

---

# Coding Rules

Always use:

* TypeScript in frontend
* Python type hints
* Clean Architecture
* Service Layer
* Repository Pattern
* DTO pattern

Never place business logic inside controllers.

Controllers should:

* Validate requests
* Call services
* Return responses

Services contain business logic.

Repositories contain database access.

---

# Security Rules

Implement:

* JWT Authentication
* Refresh Tokens
* Role-Based Access Control
* Password Hashing
* Audit Logging

Never store passwords in plain text.

Use bcrypt.

---

# UI Standards

Create:

* Responsive layout
* Sidebar navigation
* Top navigation
* Dashboard cards
* Data tables
* Search and filtering
* Pagination
* Export buttons

Use Material UI components.

---

# Inventory Rules

Negative stock is prohibited.

Every inventory movement must create ledger records.

Use FIFO valuation.

Track:

* Quantity On Hand
* Available Quantity
* Reserved Quantity
* Batch Number

---

# Sales Rules

Customer must always pass through Sales Outlet.

Customer cannot directly collect products from warehouse.

Sales approval is mandatory before loading.

Goods Issue Voucher is required before dispatch.

---

# Warehouse Rules

All warehouse movements require vouchers.

Required voucher types:

* GRV
* GIV
* Transfer Voucher
* Return Voucher
* Adjustment Voucher

Inventory must update automatically.

---

# Transfer Rules

Transfers require:

Request

Approval

Goods Issue

Transit

Goods Receive

Inventory Update

Transfer status:

* Draft
* Pending
* Approved
* In Transit
* Received
* Cancelled

---

# Audit Requirements

Log every:

* Login
* Logout
* Create
* Update
* Delete
* Approval
* Inventory Movement

Store:

* User
* Action
* Timestamp
* Branch
* IP Address

---

# Development Expectations

Generate:

* Production-ready code
* Unit tests
* API documentation
* Database migrations
* Seed data

Avoid mock implementations.

Avoid placeholder code.

Prefer reusable components.

Follow enterprise ERP standards.
