import { useEffect, useState } from 'react';
import {
  Box, TextField, Table, TableHead, TableBody, TableRow, TableCell,
  TablePagination, MenuItem, Paper, Typography, Tab, Tabs,
} from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import { storeApi, warehousesApi } from '../../api/endpoints';

export default function RawMaterialStockPage() {
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [warehouseId, setWarehouseId] = useState<number>(0);
  const [search, setSearch] = useState('');
  const [items, setItems] = useState<any[]>([]);
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    warehousesApi.list({ per_page: 1000 }).then(r => {
      setWarehouses(r.items || []);
      if ((r.items || []).length > 0) setWarehouseId(r.items[0].id);
    });
  }, []);

  const fetchStock = async () => {
    setLoading(true);
    try {
      const params: any = { page: page + 1, per_page: rowsPerPage, search };
      if (warehouseId) params.warehouse_id = warehouseId;
      const res = await storeApi.inventory.list(params);
      setItems(res.inventory || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  };

  const fetchLedger = async () => {
    setLoading(true);
    try {
      const params: any = { page: page + 1, per_page: rowsPerPage };
      if (warehouseId) params.warehouse_id = warehouseId;
      const res = await storeApi.ledger.list(params);
      setEntries(res.entries || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tab === 0) fetchStock();
    else fetchLedger();
  }, [page, rowsPerPage, tab, warehouseId]);

  useEffect(() => {
    if (page !== 0) setPage(0);
    else if (tab === 0) fetchStock();
    else fetchLedger();
  }, [search]);

  return (
    <>
      <PageHeader title="Raw Material Stock" subtitle="View stock levels and movements" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField select size="small" label="Warehouse" value={warehouseId}
          onChange={(e: any) => { setWarehouseId(Number(e.target.value)); setPage(0); }}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value={0}>All Warehouses</MenuItem>
          {warehouses.map((w: any) => (
            <MenuItem key={w.id} value={w.id}>{w.name} - {w.code}</MenuItem>
          ))}
        </TextField>
        <TextField size="small" label="Search" value={search} onChange={(e) => setSearch(e.target.value)} sx={{ minWidth: 250 }} />
      </Box>

      <Tabs value={tab} onChange={(_, v) => { setTab(v); setPage(0); }} sx={{ mb: 2 }}>
        <Tab label="Stock Levels" />
        <Tab label="Ledger (Movements)" />
      </Tabs>

      {tab === 0 && (
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Raw Material</TableCell>
                <TableCell>SKU</TableCell>
                <TableCell>Warehouse</TableCell>
                <TableCell align="right">On Hand</TableCell>
                <TableCell align="right">Reserved</TableCell>
                <TableCell align="right">Available</TableCell>
                <TableCell>Unit</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((inv: any) => (
                <TableRow key={inv.id} hover>
                  <TableCell>{inv.raw_material_name}</TableCell>
                  <TableCell>{inv.raw_material_sku}</TableCell>
                  <TableCell>{inv.warehouse_name}</TableCell>
                  <TableCell align="right">{inv.quantity_on_hand}</TableCell>
                  <TableCell align="right">{inv.reserved_quantity}</TableCell>
                  <TableCell align="right">
                    <Typography fontWeight={600} color={inv.available_quantity > 0 ? 'success.main' : 'error.main'}>
                      {inv.available_quantity}
                    </Typography>
                  </TableCell>
                  <TableCell>{inv.unit_name || '-'}</TableCell>
                </TableRow>
              ))}
              {items.length === 0 && !loading && (
                <TableRow><TableCell colSpan={7} align="center" sx={{ py: 3, color: 'text.secondary' }}>No stock records found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination component="div" count={total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={rowsPerPage} onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }} />
        </Paper>
      )}

      {tab === 1 && (
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Raw Material</TableCell>
                <TableCell>Warehouse</TableCell>
                <TableCell>Movement Type</TableCell>
                <TableCell align="right">Quantity</TableCell>
                <TableCell align="right">Unit Cost</TableCell>
                <TableCell>Reference</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((e: any) => (
                <TableRow key={e.id} hover>
                  <TableCell>{e.transaction_date ? new Date(e.transaction_date).toLocaleString() : '-'}</TableCell>
                  <TableCell>{e.raw_material_name}</TableCell>
                  <TableCell>{e.warehouse_name}</TableCell>
                  <TableCell><Typography fontWeight={500} color={e.quantity > 0 ? 'success.main' : 'error.main'}>{e.movement_type}</Typography></TableCell>
                  <TableCell align="right">{e.quantity}</TableCell>
                  <TableCell align="right">{e.unit_cost?.toFixed(2) || '-'}</TableCell>
                  <TableCell>{e.reference_type ? `${e.reference_type} #${e.reference_id}` : '-'}</TableCell>
                </TableRow>
              ))}
              {entries.length === 0 && !loading && (
                <TableRow><TableCell colSpan={7} align="center" sx={{ py: 3, color: 'text.secondary' }}>No ledger entries found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination component="div" count={total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={rowsPerPage} onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }} />
        </Paper>
      )}
    </>
  );
}
