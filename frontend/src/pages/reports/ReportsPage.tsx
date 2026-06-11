import { useState, useMemo, useEffect, useCallback } from 'react';
import {
  Box, Card, CardActionArea, Typography, Grid2 as Grid, Dialog, DialogTitle,
  DialogContent, CircularProgress,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import BarChartIcon from '@mui/icons-material/BarChart';
import AssessmentIcon from '@mui/icons-material/Assessment';
import InventoryIcon from '@mui/icons-material/Inventory';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import StoreIcon from '@mui/icons-material/Store';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing';
import PeopleIcon from '@mui/icons-material/People';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import { reportsApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import { formatCurrency } from '../../utils/format';

interface ReportCard {
  key: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  roles?: string[];
}

const reportCards: ReportCard[] = [
  { key: 'dailySales', label: 'Daily Sales', icon: <BarChartIcon />, color: '#1565c0', roles: ['Owner', 'General Manager', 'Sales Manager', 'Accountant'] },
  { key: 'monthlySales', label: 'Monthly Sales', icon: <AssessmentIcon />, color: '#00838f', roles: ['Owner', 'General Manager', 'Sales Manager', 'Accountant'] },
  { key: 'inventoryValuation', label: 'Inventory Valuation', icon: <InventoryIcon />, color: '#2e7d32', roles: ['Owner', 'General Manager', 'Warehouse Manager', 'Accountant'] },
  { key: 'inventoryMovement', label: 'Inventory Movement', icon: <SwapHorizIcon />, color: '#e65100', roles: ['Owner', 'General Manager', 'Warehouse Manager'] },
  { key: 'branchPerformance', label: 'Branch Performance', icon: <StoreIcon />, color: '#6a1b9a', roles: ['Owner', 'General Manager', 'Branch Manager'] },
  { key: 'warehouseStock', label: 'Warehouse Stock', icon: <WarehouseIcon />, color: '#1565c0', roles: ['Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper'] },
  { key: 'productionReports', label: 'Production Reports', icon: <PrecisionManufacturingIcon />, color: '#37474f', roles: ['Owner', 'General Manager', 'Production Manager'] },
  { key: 'customerBalances', label: 'Customer Balances', icon: <PeopleIcon />, color: '#00838f', roles: ['Owner', 'General Manager', 'Sales Manager', 'Accountant'] },
  { key: 'transferReports', label: 'Transfer Reports', icon: <LocalShippingIcon />, color: '#e65100', roles: ['Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper'] },
];

const reportApiMapping: Record<string, (params?: any) => Promise<any>> = {
  dailySales: reportsApi.dailySales,
  monthlySales: reportsApi.monthlySales,
  inventoryValuation: reportsApi.inventoryValuation,
  inventoryMovement: reportsApi.inventoryMovement,
  branchPerformance: reportsApi.branchPerformance,
  warehouseStock: reportsApi.warehouseStock,
  productionReports: reportsApi.production,
  customerBalances: reportsApi.customerBalances,
  transferReports: reportsApi.transfers,
};

const AMOUNT_KEYS = ['total_amount', 'subtotal', 'tax_amount', 'paid_amount', 'balance_due', 'amount', 'unit_price', 'total_price', 'unit_cost', 'total_cost', 'value', 'revenue', 'cost'];

export default function ReportsPage() {
  const { hasRole } = useAuthStore();
  const [open, setOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportCard | null>(null);
  const [reportData, setReportData] = useState<any[]>([]);
  const [reportMeta, setReportMeta] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const fetchReport = useCallback(async (card: ReportCard, from: string, to: string) => {
    setLoading(true);
    setReportMeta({});
    try {
      const fetchFn = reportApiMapping[card.key];
      if (!fetchFn) { setReportData([]); return; }
      const params: any = {};
      if (from) params.date_from = from;
      if (to) params.date_to = to;
      const data = await fetchFn(params);
      const { orders, daily_breakdown, items, entries, branches, warehouses, batches, customers, transfers, ...meta } = data || {};
      let rows: any[] = [];
      if (card.key === 'dailySales') rows = orders || [];
      else if (card.key === 'monthlySales') rows = daily_breakdown || [];
      else if (card.key === 'inventoryValuation') rows = items || [];
      else if (card.key === 'inventoryMovement') rows = entries || [];
      else if (card.key === 'branchPerformance') rows = branches || [];
      else if (card.key === 'warehouseStock') rows = warehouses || [];
      else if (card.key === 'productionReports') rows = batches || [];
      else if (card.key === 'customerBalances') rows = customers || [];
      else if (card.key === 'transferReports') rows = transfers || [];
      else rows = Array.isArray(data) ? data : [];
      setReportData(rows);
      setReportMeta(meta);
    } catch {
      setReportData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleCardClick = (card: ReportCard) => {
    setSelectedReport(card);
    setDateFrom('');
    setDateTo('');
    setOpen(true);
    fetchReport(card, '', '');
  };

  useEffect(() => {
    if (open && selectedReport) {
      fetchReport(selectedReport, dateFrom, dateTo);
    }
  }, [dateFrom, dateTo, open, selectedReport, fetchReport]);

  const handleClose = () => {
    setOpen(false);
    setSelectedReport(null);
    setReportData([]);
  };

  const columns = useMemo(() => {
    if (!reportData.length) return [];
    return Object.keys(reportData[0])
      .filter((k) => k !== 'id')
      .map((key) => ({
        id: key,
        label: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        nowrap: AMOUNT_KEYS.includes(key),
        render: AMOUNT_KEYS.includes(key)
          ? (row: any) => formatCurrency(row[key])
          : undefined,
      }));
  }, [reportData]);

  return (
    <>
      <PageHeader
        title="Reports"
        subtitle="Select a report to view"
      />

      <Grid container spacing={3}>
        {reportCards.filter(card => !card.roles || card.roles.some(r => hasRole(r))).map((card) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={card.key}>
            <Card sx={{ transition: '0.2s', '&:hover': { transform: 'translateY(-2px)', boxShadow: 4 } }}>
              <CardActionArea onClick={() => handleCardClick(card)} sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ color: '#fff', bgcolor: card.color, borderRadius: 2, p: 1.5, display: 'flex' }}>
                    {card.icon}
                  </Box>
                  <Typography variant="h6">{card.label}</Typography>
                </Box>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {selectedReport?.label}
            <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={setDateFrom} onDateToChange={setDateTo} />
          </Box>
          <Box onClick={handleClose} sx={{ cursor: 'pointer', display: 'flex' }}>
            <CloseIcon />
          </Box>
        </DialogTitle>
        <DialogContent>
          {loading ? (
            <Box sx={{ py: 4, textAlign: 'center' }}><CircularProgress /></Box>
          ) : (
            <>
              {Object.keys(reportMeta).length > 0 && (
                <Box sx={{ mb: 2, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                  {Object.entries(reportMeta).map(([key, val]) =>
                    typeof val === 'number' || typeof val === 'string' ? (
                      <Typography key={key} variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {key.replace(/_/g, ' ')}: <strong>{typeof val === 'number' ? Number(val).toLocaleString() : val}</strong>
                      </Typography>
                    ) : null
                  )}
                </Box>
              )}
              <DataTable
                columns={columns}
                data={reportData}
                loading={loading}
                total={reportData.length}
              />
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
