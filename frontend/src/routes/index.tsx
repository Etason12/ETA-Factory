import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import MainLayout from '../components/layout/MainLayout';
import LoginPage from '../pages/auth/LoginPage';
import DashboardPage from '../pages/dashboard/DashboardPage';
import ProductsPage from '../pages/products/ProductsPage';
import ProductFormPage from '../pages/products/ProductFormPage';
import CustomersPage from '../pages/customers/CustomersPage';
import CustomerFormPage from '../pages/customers/CustomerFormPage';
import SalesOrdersPage from '../pages/sales/SalesOrdersPage';
import SalesOrderFormPage from '../pages/sales/SalesOrderFormPage';
import SalesOrderDetailPage from '../pages/sales/SalesOrderDetailPage';
import SalesQuotationsPage from '../pages/sales/SalesQuotationsPage';
import SalesQuotationFormPage from '../pages/sales/SalesQuotationFormPage';
import InvoicesPage from '../pages/sales/InvoicesPage';
import InvoiceFormPage from '../pages/sales/InvoiceFormPage';
import PaymentsPage from '../pages/sales/PaymentsPage';
import LoadingAuthorizationsPage from '../pages/sales/LoadingAuthorizationsPage';
import ProductionBatchesPage from '../pages/production/ProductionBatchesPage';
import ProductionBatchFormPage from '../pages/production/ProductionBatchFormPage';
import StocktakePage from '../pages/warehouse/StocktakePage';
import StockAdjustmentPage from '../pages/warehouse/StockAdjustmentPage';
import WarehouseListPage from '../pages/warehouse/WarehouseListPage';
import GRVListPage from '../pages/warehouse/GRVListPage';
import GIVListPage from '../pages/warehouse/GIVListPage';
import DisposalVoucherPage from '../pages/warehouse/DisposalVoucherPage';
import TransfersPage from '../pages/transfers/TransfersPage';
import TransferFormPage from '../pages/transfers/TransferFormPage';
import InventoryPage from '../pages/inventory/InventoryPage';
import InventoryLedgerPage from '../pages/inventory/InventoryLedgerPage';
import OpeningBalancePage from '../pages/inventory/OpeningBalancePage';
import InventoryDashboardPage from '../pages/inventory/InventoryDashboardPage';
import LowStockPage from '../pages/inventory/LowStockPage';
import BinCardPage from '../pages/inventory/BinCardPage';
import UsersPage from '../pages/users/UsersPage';
import UserFormPage from '../pages/users/UserFormPage';
import BranchesPage from '../pages/branches/BranchesPage';
import BranchFormPage from '../pages/branches/BranchFormPage';
import LedgerReconciliationReportPage from '../pages/reports/LedgerReconciliationReportPage';
import ReportsPage from '../pages/reports/ReportsPage';
import AuditLogsPage from '../pages/audit/AuditLogsPage';
import SettingsPage from '../pages/settings/index';
import RolesListPage from '../pages/roles/RolesListPage';
import RoleFormPage from '../pages/roles/RoleFormPage';
import RolePermissionsPage from '../pages/roles/RolePermissionsPage';
import BOMManagementPage from '../pages/products/BOMManagementPage';
import RawMaterialsPage from '../pages/raw_materials/RawMaterialsPage';
import RawMaterialFormPage from '../pages/raw_materials/RawMaterialFormPage';
import SuppliersPage from '../pages/suppliers/SuppliersPage';
import SupplierFormPage from '../pages/suppliers/SupplierFormPage';
import PurchaseOrdersPage from '../pages/purchasing/PurchaseOrdersPage';
import PurchaseOrderFormPage from '../pages/purchasing/PurchaseOrderFormPage';
import StoreRequisitionsPage from '../pages/store/StoreRequisitionsPage';
import StoreRequisitionFormPage from '../pages/store/StoreRequisitionFormPage';
import RawMaterialStockPage from '../pages/store/RawMaterialStockPage';
import CategoryListPage from '../pages/settings/CategoryListPage';
import UnitListPage from '../pages/settings/UnitListPage';

function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, hasRole } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (roles && !roles.some((r) => hasRole(r))) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="products/new" element={<ProductFormPage />} />
          <Route path="products/:id/edit" element={<ProductFormPage />} />
          <Route path="products/:id/view" element={<ProductFormPage />} />
          <Route path="products/:productId/bom" element={<BOMManagementPage />} />
          <Route path="raw-materials" element={<RawMaterialsPage />} />
          <Route path="raw-materials/new" element={<RawMaterialFormPage />} />
          <Route path="raw-materials/:rawMaterialId/edit" element={<RawMaterialFormPage />} />
          <Route path="raw-materials/:rawMaterialId/view" element={<RawMaterialFormPage />} />
          <Route path="customers" element={<CustomersPage />} />
          <Route path="customers/new" element={<CustomerFormPage />} />
          <Route path="customers/:id/edit" element={<CustomerFormPage />} />
          <Route path="sales/orders" element={<SalesOrdersPage />} />
          <Route path="sales/orders/new" element={<SalesOrderFormPage />} />
          <Route path="sales/orders/:id" element={<SalesOrderDetailPage />} />
          <Route path="sales/orders/:id/edit" element={<SalesOrderFormPage />} />
          <Route path="sales/quotations" element={<SalesQuotationsPage />} />
          <Route path="sales/quotations/new" element={<SalesQuotationFormPage />} />
          <Route path="sales/quotations/:id" element={<SalesQuotationFormPage />} />
          <Route path="sales/quotations/:id/edit" element={<SalesQuotationFormPage />} />
          <Route path="sales/invoices" element={<InvoicesPage />} />
          <Route path="sales/invoices/new" element={<InvoiceFormPage />} />
          <Route path="sales/payments" element={<PaymentsPage />} />
          <Route path="sales/loading-authorizations" element={<LoadingAuthorizationsPage />} />
          <Route path="production/batches" element={<ProductionBatchesPage />} />
          <Route path="production/batches/new" element={<ProductionBatchFormPage />} />
          <Route path="production/batches/:id/edit" element={<ProductionBatchFormPage />} />
          <Route path="warehouses" element={<WarehouseListPage />} />
          <Route path="warehouses/adjustments" element={<StockAdjustmentPage />} />
          <Route path="warehouses/stocktake" element={<StocktakePage />} />
          <Route path="warehouses/grv" element={<GRVListPage />} />
          <Route path="warehouses/giv" element={<GIVListPage />} />
          <Route path="warehouses/disposal" element={<DisposalVoucherPage />} />
          <Route path="transfers" element={<TransfersPage />} />
          <Route path="transfers/new" element={<TransferFormPage />} />
          <Route path="transfers/:id/edit" element={<TransferFormPage />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="inventory/dashboard" element={<InventoryDashboardPage />} />
          <Route path="inventory/ledger" element={<InventoryLedgerPage />} />
          <Route path="inventory/opening-balances" element={<OpeningBalancePage />} />
          <Route path="inventory/low-stock" element={<LowStockPage />} />
          <Route path="inventory/bin-card" element={<BinCardPage />} />
          <Route path="users" element={<ProtectedRoute roles={['Owner', 'General Manager']}><UsersPage /></ProtectedRoute>} />
          <Route path="users/new" element={<ProtectedRoute roles={['Owner', 'General Manager']}><UserFormPage /></ProtectedRoute>} />
          <Route path="users/:id/edit" element={<ProtectedRoute roles={['Owner', 'General Manager']}><UserFormPage /></ProtectedRoute>} />
          <Route path="branches" element={<ProtectedRoute roles={['Owner', 'General Manager']}><BranchesPage /></ProtectedRoute>} />
          <Route path="branches/new" element={<ProtectedRoute roles={['Owner', 'General Manager']}><BranchFormPage /></ProtectedRoute>} />
          <Route path="branches/:id/edit" element={<ProtectedRoute roles={['Owner', 'General Manager']}><BranchFormPage /></ProtectedRoute>} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="reports/ledger-reconciliation" element={<LedgerReconciliationReportPage />} />
          <Route path="audit" element={<ProtectedRoute roles={['Owner', 'General Manager', 'Auditor']}><AuditLogsPage /></ProtectedRoute>} />
          <Route path="settings" element={<ProtectedRoute roles={['Owner']}><SettingsPage /></ProtectedRoute>} />
          <Route path="settings/categories" element={<CategoryListPage />} />
          <Route path="settings/units" element={<UnitListPage />} />
          <Route path="roles" element={<ProtectedRoute roles={['Owner', 'General Manager']}><RolesListPage /></ProtectedRoute>} />
          <Route path="roles/new" element={<ProtectedRoute roles={['Owner', 'General Manager']}><RoleFormPage /></ProtectedRoute>} />
          <Route path="roles/:id/edit" element={<ProtectedRoute roles={['Owner', 'General Manager']}><RoleFormPage /></ProtectedRoute>} />
          <Route path="roles/permissions" element={<ProtectedRoute roles={['Owner', 'General Manager']}><RolePermissionsPage /></ProtectedRoute>} />
          <Route path="suppliers" element={<SuppliersPage />} />
          <Route path="suppliers/new" element={<SupplierFormPage />} />
          <Route path="suppliers/:id/edit" element={<SupplierFormPage />} />
          <Route path="suppliers/:id/view" element={<SupplierFormPage />} />
          <Route path="purchasing/orders" element={<PurchaseOrdersPage />} />
          <Route path="purchasing/orders/new" element={<PurchaseOrderFormPage />} />
          <Route path="purchasing/orders/:id" element={<PurchaseOrderFormPage />} />
          <Route path="purchasing/orders/:id/edit" element={<PurchaseOrderFormPage />} />
          <Route path="store/requisitions" element={<StoreRequisitionsPage />} />
          <Route path="store/requisitions/new" element={<StoreRequisitionFormPage />} />
          <Route path="store/requisitions/:id" element={<StoreRequisitionFormPage />} />
          <Route path="store/stock" element={<RawMaterialStockPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
