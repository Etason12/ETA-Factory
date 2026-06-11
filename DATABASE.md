# DATABASE.md

## Core Tables

### users

* id
* username
* email
* password_hash
* role_id
* branch_id
* is_active
* created_at

### roles

* id
* name
* description

### permissions

* id
* name

### role_permissions

* id
* role_id
* permission_id

### branches

* id
* name
* code
* city
* address

### warehouses

* id
* branch_id
* name
* type

Types:

* Factory
* Branch Warehouse
* Sales Store

### customers

* id
* customer_code
* name
* phone
* address
* tin_number

### product_categories

* id
* name

### units

* id
* name
* abbreviation

### products

* id
* sku
* name
* category_id
* unit_id

### production_batches

* id
* batch_number
* product_id
* quantity
* production_date
* warehouse_id

### inventory

* id
* product_id
* warehouse_id
* quantity_on_hand
* reserved_quantity

### inventory_ledger

* id
* product_id
* warehouse_id
* movement_type
* quantity
* reference_type
* reference_id
* transaction_date

### sales_orders

* id
* order_number
* customer_id
* branch_id
* status

### invoices

* id
* invoice_number
* sales_order_id
* total_amount
* payment_status

### payments

* id
* invoice_id
* amount
* payment_method

### goods_issue_vouchers

* id
* voucher_number
* warehouse_id
* sales_order_id

### goods_receive_vouchers

* id
* voucher_number
* warehouse_id

### transfers

* id
* transfer_number
* source_warehouse_id
* destination_warehouse_id
* status

### transfer_items

* id
* transfer_id
* product_id
* quantity

### audit_logs

* id
* user_id
* action
* module
* timestamp

---

# Relationships

Branch

→ Warehouses

→ Users

→ Sales Orders

Warehouse

→ Inventory

→ Transfers

→ GRV

→ GIV

Product

→ Inventory

→ Production

→ Sales

Customer

→ Sales Orders

→ Invoices

→ Payments

Every inventory transaction must create a ledger entry.

Ledger is the source of truth for stock movement history.