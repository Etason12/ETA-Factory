import apiClient from './client';
import type {
  User, Branch, Warehouse, Product, ProductCategory, Unit,
  Customer, Inventory, InventoryLedger, ProductionBatch,
  SalesQuotation, SalesOrder, Invoice, Payment,
  GoodsReceiveVoucher, GoodsIssueVoucher, DisposalVoucher, Transfer,
  LoadingAuthorization, AuditLog, PaginatedResponse,
  LoginRequest, LoginResponse, DashboardMetrics, Company,
} from '../types';

export const authApi = {
  login: (data: LoginRequest) => apiClient.post<LoginResponse>('/auth/login', data).then(r => r.data),
  refresh: (refresh_token: string) => apiClient.post<{ access_token: string }>('/auth/refresh', { refresh_token }).then(r => r.data),
  changePassword: (data: { old_password: string; new_password: string }) => apiClient.post('/auth/change-password', data).then(r => r.data),
  me: () => apiClient.get<any>('/auth/me').then(r => r.data.user),
};

export const usersApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<User>>('/users', { params }).then(r => r.data),
  create: (data: Partial<User>) => apiClient.post<User>('/users', data).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/users/${id}`).then(r => r.data.user || r.data),
  update: (id: number, data: Partial<User>) => apiClient.put<User>(`/users/${id}`, data).then(r => r.data),
  delete: (id: number) => apiClient.delete(`/users/${id}`).then(r => r.data),
};

export const branchesApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<Branch>>('/branches', { params }).then(r => r.data),
  create: (data: Partial<Branch>) => apiClient.post<Branch>('/branches', data).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/branches/${id}`).then(r => r.data.branch || r.data),
  update: (id: number, data: Partial<Branch>) => apiClient.put<Branch>(`/branches/${id}`, data).then(r => r.data),
  delete: (id: number) => apiClient.delete(`/branches/${id}`).then(r => r.data),
};

export const warehousesApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<Warehouse>>('/warehouses', { params }).then(r => r.data),
  create: (data: Partial<Warehouse>) => apiClient.post<Warehouse>('/warehouses', data).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/warehouses/${id}`).then(r => r.data.warehouse || r.data),
  update: (id: number, data: Partial<Warehouse>) => apiClient.put<Warehouse>(`/warehouses/${id}`, data).then(r => r.data),
  delete: (id: number) => apiClient.delete(`/warehouses/${id}`).then(r => r.data),
  inventory: (id: number) => apiClient.get<any>(`/warehouses/${id}/inventory`).then(r => r.data.inventory || []),
  grvList: (params?: any) => apiClient.get<PaginatedResponse<GoodsReceiveVoucher>>('/warehouses/grv', { params }).then(r => r.data),
  createGrv: (data: any) => apiClient.post<GoodsReceiveVoucher>('/warehouses/grv', data).then(r => r.data),
  getGrv: (id: number) => apiClient.get<any>(`/warehouses/grv/${id}`).then(r => r.data.grv || r.data),
  approveGrv: (id: number) => apiClient.put(`/warehouses/grv/${id}/approve`).then(r => r.data),
  givList: (params?: any) => apiClient.get<PaginatedResponse<GoodsIssueVoucher>>('/warehouses/giv', { params }).then(r => r.data),
  createGiv: (data: any) => apiClient.post<GoodsIssueVoucher>('/warehouses/giv', data).then(r => r.data),
  getGiv: (id: number) => apiClient.get<any>(`/warehouses/giv/${id}`).then(r => r.data.giv || r.data),
  approveGiv: (id: number) => apiClient.put(`/warehouses/giv/${id}/approve`).then(r => r.data),
  disposalList: (params?: any) => apiClient.get<any>('/warehouses/disposal', { params }).then(r => r.data),
  createDisposal: (data: any) => apiClient.post<any>('/warehouses/disposal', data).then(r => r.data),
  getDisposal: (id: number) => apiClient.get<any>(`/warehouses/disposal/${id}`).then(r => r.data.disposal || r.data),
  approveDisposal: (id: number) => apiClient.put(`/warehouses/disposal/${id}/approve`).then(r => r.data),
  listAdjustments: (params?: any) => apiClient.get<any>('/warehouses/adjustments', { params }).then(r => r.data),
  createAdjustment: (data: any) => apiClient.post<any>('/warehouses/adjustments', data).then(r => r.data),
};

export const productsApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<Product>>('/products', { params }).then(r => r.data),
  create: (data: Partial<Product>) => apiClient.post<Product>('/products', data).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/products/${id}`).then(r => r.data.product || r.data),
  update: (id: number, data: Partial<Product>) => apiClient.put<Product>(`/products/${id}`, data).then(r => r.data),
  delete: (id: number) => apiClient.delete(`/products/${id}`).then(r => r.data),
  categories: () => apiClient.get<any>('/products/categories').then(r => r.data.categories || []),
  createCategory: (data: Partial<ProductCategory>) => apiClient.post<any>('/products/categories', data).then(r => r.data),
  updateCategory: (id: number, data: Partial<ProductCategory>) => apiClient.put<any>(`/products/categories/${id}`, data).then(r => r.data),
  deleteCategory: (id: number) => apiClient.delete(`/products/categories/${id}`).then(r => r.data),
  units: () => apiClient.get<any>('/products/units').then(r => r.data.units || []),
  createUnit: (data: Partial<Unit>) => apiClient.post<any>('/products/units', data).then(r => r.data),
  updateUnit: (id: number, data: Partial<Unit>) => apiClient.put<any>(`/products/units/${id}`, data).then(r => r.data),
  deleteUnit: (id: number) => apiClient.delete(`/products/units/${id}`).then(r => r.data),
};

export const customersApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<Customer>>('/customers', { params }).then(r => r.data),
  create: (data: Partial<Customer>) => apiClient.post<Customer>('/customers', data).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/customers/${id}`).then(r => r.data.customer || r.data),
  update: (id: number, data: Partial<Customer>) => apiClient.put<Customer>(`/customers/${id}`, data).then(r => r.data),
  delete: (id: number) => apiClient.delete(`/customers/${id}`).then(r => r.data),
  history: (id: number) => apiClient.get(`/customers/${id}/history`).then(r => r.data),
};

export const inventoryApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<Inventory>>('/inventory', { params }).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/inventory/${id}`).then(r => r.data.inventory || r.data),
  update: (id: number, data: any) => apiClient.put(`/inventory/${id}`, data).then(r => r.data),
  byWarehouse: (id: number) => apiClient.get<any>(`/inventory/warehouse/${id}`).then(r => r.data.items || []),
  ledger: (params?: any) => apiClient.get<PaginatedResponse<InventoryLedger>>('/inventory/ledger', { params }).then(r => r.data),
  productLedger: (id: number) => apiClient.get<any>(`/inventory/ledger/product/${id}`).then(r => r.data.items || []),
  summary: () => apiClient.get<any>('/inventory/summary').then(r => r.data),
  lowStock: (params?: any) => apiClient.get<any>('/inventory/low-stock', { params }).then(r => r.data),
  binCard: (params: any) => apiClient.get<any>('/inventory/bin-card', { params }).then(r => r.data),
  openingBalances: {
    list: (params?: any) => apiClient.get('/inventory/opening-balances', { params }).then(r => r.data),
    create: (data: any) => apiClient.post('/inventory/opening-balances', data).then(r => r.data),
  },
};

export const productionApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<ProductionBatch>>('/production/batches', { params }).then(r => r.data),
  create: (data: Partial<ProductionBatch>) => apiClient.post<ProductionBatch>('/production/batches', data).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/production/batches/${id}`).then(r => r.data.batch || r.data),
  approve: (id: number) => apiClient.put(`/production/batches/${id}/approve`).then(r => r.data),
  cancel: (id: number) => apiClient.put(`/production/batches/${id}/cancel`).then(r => r.data),
};

export const salesApi = {
  quotations: {
    list: (params?: any) => apiClient.get<PaginatedResponse<SalesQuotation>>('/sales/quotations', { params }).then(r => r.data),
    create: (data: any) => apiClient.post<SalesQuotation>('/sales/quotations', data).then(r => r.data),
    get: (id: number) => apiClient.get<any>(`/sales/quotations/${id}`).then(r => r.data.quotation || r.data),
    update: (id: number, data: any) => apiClient.put<SalesQuotation>(`/sales/quotations/${id}`, data).then(r => r.data),
    delete: (id: number) => apiClient.delete(`/sales/quotations/${id}`).then(r => r.data),
    convert: (id: number) => apiClient.post(`/sales/quotations/${id}/convert`).then(r => r.data),
  },
  orders: {
    list: (params?: any) => apiClient.get<PaginatedResponse<SalesOrder>>('/sales/orders', { params }).then(r => r.data),
    create: (data: any) => apiClient.post<SalesOrder>('/sales/orders', data).then(r => r.data),
    get: (id: number) => apiClient.get<any>(`/sales/orders/${id}`).then(r => r.data.order || r.data),
    approve: (id: number) => apiClient.put(`/sales/orders/${id}/approve`).then(r => r.data),
    cancel: (id: number) => apiClient.put(`/sales/orders/${id}/cancel`).then(r => r.data),
  },
  invoices: {
    list: (params?: any) => apiClient.get<PaginatedResponse<Invoice>>('/sales/invoices', { params }).then(r => r.data),
    create: (data: any) => apiClient.post<Invoice>('/sales/invoices', data).then(r => r.data),
    get: (id: number) => apiClient.get<any>(`/sales/invoices/${id}`).then(r => r.data.invoice || r.data),
    pay: (id: number, data: any) => apiClient.put(`/sales/invoices/${id}/pay`, data).then(r => r.data),
  },
  payments: {
    list: (params?: any) => apiClient.get<PaginatedResponse<Payment>>('/sales/payments', { params }).then(r => r.data),
  },
  loadingAuthorizations: {
    list: (params?: any) => apiClient.get<PaginatedResponse<LoadingAuthorization>>('/sales/loading-authorizations', { params }).then(r => r.data),
    create: (data: any) => apiClient.post<LoadingAuthorization>('/sales/loading-authorizations', data).then(r => r.data),
    approve: (id: number) => apiClient.put(`/sales/loading-authorizations/${id}/approve`).then(r => r.data),
  },
};

export const transfersApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<Transfer>>('/transfers', { params }).then(r => r.data),
  create: (data: any) => apiClient.post<Transfer>('/transfers', data).then(r => r.data),
  get: (id: number) => apiClient.get<any>(`/transfers/${id}`).then(r => r.data.transfer || r.data),
  approve: (id: number) => apiClient.put(`/transfers/${id}/approve`).then(r => r.data),
  issue: (id: number) => apiClient.put(`/transfers/${id}/issue`).then(r => r.data),
  receive: (id: number) => apiClient.put(`/transfers/${id}/receive`).then(r => r.data),
  cancel: (id: number) => apiClient.put(`/transfers/${id}/cancel`).then(r => r.data),
};

export const reportsApi = {
  dailySales: (params?: any) => apiClient.get('/reports/daily-sales', { params }).then(r => r.data),
  monthlySales: (params?: any) => apiClient.get('/reports/monthly-sales', { params }).then(r => r.data),
  inventoryValuation: () => apiClient.get('/reports/inventory-valuation').then(r => r.data),
  inventoryMovement: (params?: any) => apiClient.get('/reports/inventory-movement', { params }).then(r => r.data),
  branchPerformance: (params?: any) => apiClient.get('/reports/branch-performance', { params }).then(r => r.data),
  warehouseStock: (params?: any) => apiClient.get('/reports/warehouse-stock', { params }).then(r => r.data),
  production: (params?: any) => apiClient.get('/reports/production', { params }).then(r => r.data),
  customerBalances: () => apiClient.get('/reports/customer-balances').then(r => r.data),
  transfers: (params?: any) => apiClient.get('/reports/transfers', { params }).then(r => r.data),
};

export const companyApi = {
  get: () => apiClient.get<{ company: Company | null }>('/company').then(r => r.data.company),
  update: (data: Partial<Company>) => apiClient.put<{ company: Company }>('/company', data).then(r => r.data.company),
};

export const auditApi = {
  list: (params?: any) => apiClient.get<PaginatedResponse<AuditLog>>('/audit/logs', { params }).then(r => r.data),
};
