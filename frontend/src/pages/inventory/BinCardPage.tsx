import { useEffect, useState } from 'react';
import {
  Box, Paper, Typography, TextField, MenuItem, Grid2 as Grid, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Chip, FormControl, InputLabel, Select, Button, CircularProgress, Alert,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import PageHeader from '../../components/common/PageHeader';
import { inventoryApi, warehousesApi, productsApi } from '../../api/endpoints';
import type { Warehouse, Product } from '../../types';

export default function BinCardPage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | ''>('');
  const [productId, setProductId] = useState<number | ''>('');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    Promise.all([
      warehousesApi.list({ per_page: 1000 }),
      productsApi.list({ per_page: 1000 }),
    ]).then(([wRes, pRes]) => {
      setWarehouses(wRes.items);
      setProducts(pRes.items);
    });
  }, []);

  const handleSearch = async () => {
    if (!productId || !warehouseId) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await inventoryApi.binCard({ product_id: productId, warehouse_id: warehouseId, year, month });
      setReport(res);
    } finally {
      setLoading(false);
    }
  };

  const months = [
    { value: 1, label: 'January' }, { value: 2, label: 'February' }, { value: 3, label: 'March' },
    { value: 4, label: 'April' }, { value: 5, label: 'May' }, { value: 6, label: 'June' },
    { value: 7, label: 'July' }, { value: 8, label: 'August' }, { value: 9, label: 'September' },
    { value: 10, label: 'October' }, { value: 11, label: 'November' }, { value: 12, label: 'December' },
  ];
  const years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - 5 + i);

  return (
    <Box>
      <PageHeader title="Bin Card" subtitle="Monthly stock movement report per product" />
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Grid container spacing={2} alignItems="flex-end">
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Product *</InputLabel>
              <Select value={productId} label="Product *" onChange={(e) => setProductId(e.target.value as number | '')}>
                <MenuItem value="">Select product</MenuItem>
                {products.map(p => <MenuItem key={p.id} value={p.id}>{p.name} ({p.sku})</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Warehouse *</InputLabel>
              <Select value={warehouseId} label="Warehouse *" onChange={(e) => setWarehouseId(e.target.value as number | '')}>
                <MenuItem value="">Select warehouse</MenuItem>
                {warehouses.map(w => <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 6, sm: 3, md: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Month</InputLabel>
              <Select value={month} label="Month" onChange={(e) => setMonth(Number(e.target.value))}>
                {months.map(m => <MenuItem key={m.value} value={m.value}>{m.label}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 6, sm: 3, md: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Year</InputLabel>
              <Select value={year} label="Year" onChange={(e) => setYear(Number(e.target.value))}>
                {years.map(y => <MenuItem key={y} value={y}>{y}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 3, md: 2 }}>
            <Button variant="contained" fullWidth startIcon={<SearchIcon />} onClick={handleSearch} disabled={!productId || !warehouseId || loading}>
              {loading ? 'Loading...' : 'Generate'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {loading && <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>}

      {report && !loading && (
        <Paper sx={{ borderRadius: 2, overflow: 'hidden' }}>
          {!report.has_opening_balance && (
            <Alert severity="info" sx={{ borderRadius: 0 }}>
              No opening balance was set for this product. Visit{' '}
              <Button size="small" variant="text" sx={{ textTransform: 'none', p: 0, minWidth: 'auto', verticalAlign: 'baseline' }}
                onClick={() => window.location.href = '/inventory/opening-balances'}>
                Opening Balances
              </Button>{' '}
              to set one if this product should have starting stock.
            </Alert>
          )}
          <Box sx={{ p: 3, bgcolor: '#f5f5f5', borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6">{report.product_name} ({report.product_sku})</Typography>
            <Typography variant="body2" color="text.secondary">
              {report.warehouse_name} — {months.find(m => m.value === report.month)?.label} {report.year}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 3, p: 3, bgcolor: '#e3f2fd' }}>
            <Box><Typography variant="caption" color="text.secondary">Opening Balance</Typography><Typography variant="h6">{report.opening_balance}</Typography></Box>
            <Box><Typography variant="caption" color="text.secondary">Total Inflow</Typography><Typography variant="h6" color="success.main">+{report.total_inflow}</Typography></Box>
            <Box><Typography variant="caption" color="text.secondary">Total Outflow</Typography><Typography variant="h6" color="error.main">{report.total_outflow}</Typography></Box>
            <Box><Typography variant="caption" color="text.secondary">Closing Balance</Typography><Typography variant="h6">{report.closing_balance}</Typography></Box>
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Movement Type</TableCell>
                  <TableCell>Reference</TableCell>
                  <TableCell>Batch</TableCell>
                  <TableCell align="right">In</TableCell>
                  <TableCell align="right">Out</TableCell>
                  <TableCell align="right">Balance</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell colSpan={4}><Typography fontWeight={600}>Opening Balance</Typography></TableCell>
                  <TableCell align="right" colSpan={3}><Typography fontWeight={600}>{report.opening_balance}</Typography></TableCell>
                </TableRow>
                {report.entries.length === 0 ? (
                  <TableRow><TableCell colSpan={7} align="center">No movements this month</TableCell></TableRow>
                ) : report.entries.map((e: any) => (
                  <TableRow key={e.id}>
                    <TableCell>{e.date ? new Date(e.date).toLocaleDateString() : '-'}</TableCell>
                    <TableCell><Chip label={e.movement_type} size="small" variant="outlined" /></TableCell>
                    <TableCell>{e.reference_type ? `${e.reference_type}#${e.reference_id}` : '-'}</TableCell>
                    <TableCell>{e.batch_number || '-'}</TableCell>
                    <TableCell align="right" sx={{ color: 'success.main' }}>{e.quantity > 0 ? e.quantity : '-'}</TableCell>
                    <TableCell align="right" sx={{ color: 'error.main' }}>{e.quantity < 0 ? Math.abs(e.quantity) : '-'}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>{e.running_balance}</TableCell>
                  </TableRow>
                ))}
                <TableRow sx={{ bgcolor: '#e3f2fd' }}>
                  <TableCell colSpan={4}><Typography fontWeight={600}>Closing Balance</Typography></TableCell>
                  <TableCell align="right" colSpan={3}><Typography fontWeight={700}>{report.closing_balance}</Typography></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Box>
  );
}