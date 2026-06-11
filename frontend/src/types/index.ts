export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  phone?: string;
  is_active: boolean;
  role_id: number;
  role_name: string;
  branch_id?: number;
  last_login?: string;
  created_at: string;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  is_system: boolean;
}

export interface Permission {
  id: number;
  name: string;
  description: string;
  module: string;
}

export interface Branch {
  id: number;
  name: string;
  code: string;
  city?: string;
  address?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
}

export interface Warehouse {
  id: number;
  name: string;
  code: string;
  type: string;
  address?: string;
  is_active: boolean;
  branch_id: number;
  branch_name?: string;
}

export interface ProductCategory {
  id: number;
  name: string;
  description?: string;
}

export interface Unit {
  id: number;
  name: string;
  abbreviation: string;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  description?: string;
  unit_price: number;
  cost_price: number;
  category_id: number;
  category_name?: string;
  unit_id: number;
  unit_name?: string;
  is_active: boolean;
  min_stock_level?: number;
  max_stock_level?: number;
}

export interface Customer {
  id: number;
  customer_code: string;
  name: string;
  phone?: string;
  email?: string;
  address?: string;
  tin_number?: string;
  customer_type: string;
  credit_limit: number;
  is_active: boolean;
  branch_id: number;
}

export interface Inventory {
  id: number;
  product_id: number;
  product_name?: string;
  product_sku?: string;
  warehouse_id: number;
  warehouse_name?: string;
  quantity_on_hand: number;
  reserved_quantity: number;
  available_quantity: number;
  batch_number?: string;
  min_stock_level?: number;
  max_stock_level?: number;
}

export interface InventoryLedger {
  id: number;
  product_id: number;
  warehouse_id: number;
  movement_type: string;
  quantity: number;
  unit_cost?: number;
  reference_type?: string;
  reference_id?: number;
  batch_number?: string;
  transaction_date: string;
}

export interface ProductionBatch {
  id: number;
  batch_number: string;
  product_id: number;
  product_name?: string;
  quantity_produced: number;
  production_cost: number;
  production_date: string;
  warehouse_id: number;
  warehouse_name?: string;
  notes?: string;
  status: string;
  created_by_name?: string;
  approved_by_name?: string;
  approved_at?: string;
}

export interface SalesQuotation {
  id: number;
  quotation_number: string;
  customer_id: number;
  customer_name?: string;
  branch_id: number;
  status: string;
  valid_until?: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  notes?: string;
  items: SalesQuotationItem[];
}

export interface SalesQuotationItem {
  id: number;
  quotation_id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface SalesOrder {
  id: number;
  order_number: string;
  customer_id: number;
  customer_name?: string;
  branch_id: number;
  warehouse_id: number;
  warehouse_name?: string;
  order_date: string;
  status: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  notes?: string;
  items: SalesOrderItem[];
}

export interface SalesOrderItem {
  id: number;
  sales_order_id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  delivered_quantity: number;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  sales_order_id: number;
  customer_id: number;
  customer_name?: string;
  invoice_date: string;
  due_date?: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  balance_due: number;
  payment_status: string;
  status: string;
}

export interface Payment {
  id: number;
  payment_number: string;
  invoice_id: number;
  invoice_number?: string;
  customer_id: number;
  customer_name?: string;
  amount: number;
  payment_date: string;
  payment_method: string;
  reference_number?: string;
  bank_name?: string;
  receipt_image?: string;
  notes?: string;
}

export interface GoodsReceiveVoucher {
  id: number;
  voucher_number: string;
  warehouse_id: number;
  warehouse_name?: string;
  voucher_date: string;
  reference_type?: string;
  reference_id?: number;
  notes?: string;
  status: string;
  created_by_name?: string;
  received_by_name?: string;
  items: GRVItem[];
}

export interface GRVItem {
  id: number;
  grv_id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_cost?: number;
  batch_number?: string;
}

export interface GoodsIssueVoucher {
  id: number;
  voucher_number: string;
  warehouse_id: number;
  warehouse_name?: string;
  sales_order_id?: number;
  voucher_date: string;
  reference_type?: string;
  reference_id?: number;
  notes?: string;
  status: string;
  created_by_name?: string;
  issued_by_name?: string;
  items: GIVItem[];
}

export interface GIVItem {
  id: number;
  giv_id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  batch_number?: string;
}

export interface DisposalVoucher {
  id: number;
  voucher_number: string;
  warehouse_id: number;
  warehouse_name?: string;
  voucher_date: string;
  reason: string;
  notes?: string;
  status: string;
  created_by_name?: string;
  disposed_by_name?: string;
  items: DisposalVoucherItem[];
}

export interface DisposalVoucherItem {
  id: number;
  disposal_id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  batch_number?: string;
  reason?: string;
}

export interface Transfer {
  id: number;
  transfer_number: string;
  source_warehouse_id: number;
  source_warehouse_name?: string;
  destination_warehouse_id: number;
  destination_warehouse_name?: string;
  transfer_date: string;
  status: string;
  notes?: string;
  items: TransferItem[];
}

export interface TransferItem {
  id: number;
  transfer_id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_cost?: number;
  batch_number?: string;
}

export interface LoadingAuthorization {
  id: number;
  authorization_number: string;
  sales_order_id: number;
  warehouse_id: number;
  authorized_date: string;
  status: string;
  notes?: string;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  username?: string;
  action: string;
  module: string;
  description?: string;
  entity_type?: string;
  entity_id?: number;
  branch_id?: number;
  ip_address?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface Company {
  id: number;
  name: string;
  legal_name?: string;
  tax_id?: string;
  logo_url?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  currency: string;
  fiscal_year_start?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DashboardMetrics {
  total_products: number;
  total_customers: number;
  total_orders: number;
  total_invoices: number;
  total_revenue: number;
  pending_transfers: number;
  low_stock_items: number;
  production_batches: number;
}
