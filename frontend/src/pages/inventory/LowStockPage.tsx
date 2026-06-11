import { useCallback, useEffect, useState } from 'react';
import {
  Box, TextField, MenuItem, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Typography, Chip, FormControl, InputLabel, Select,
} from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { inventoryApi, warehousesApi } from '../../api/endpoints';
import type { Warehouse } from '../../types';

export default function LowStockPage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | ''>('');
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    warehousesApi.list({ per_page: 1000 }).then(res => setWarehouses(res.items));
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: 20 };
      if (warehouseId) params.warehouse_id = warehouseId;
      const res = await inventoryApi.lowStock(params);
      setData(res.low_stock_items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, warehouseId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <Box>
      <PageHeader title="Low Stock Alerts" subtitle="Products below minimum stock level" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <FormControl size="small" sx={{ width: 250 }}>
          <InputLabel>Warehouse</InputLabel>
          <Select value={warehouseId} label="Warehouse" onChange={(e) => { setWarehouseId(e.target.value as number | ''); setPage(1); }}>
            <MenuItem value="">All</MenuItem>
            {warehouses.map(w => <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>
      {data.length === 0 && !loading ? (
        <Paper sx={{ p: 4, textAlign: 'center', borderRadius: 2, bgcolor: '#e8f5e9' }}>
          <Typography variant="h6" color="success.main">All items are adequately stocked</Typography>
          <Typography variant="body2" color="text.secondary">No products below their minimum stock level.</Typography>
        </Paper>
      ) : (
        <DataTable
          columns={[
            { id: 'product_name', label: 'Product' },
            { id: 'product_sku', label: 'SKU' },
            { id: 'warehouse_name', label: 'Warehouse' },
            { id: 'quantity_on_hand', label: 'On Hand' },
            { id: 'min_stock_level', label: 'Min Level' },
            {
              id: 'shortage', label: 'Shortage',
              render: (row: any) => (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <WarningAmberIcon color="warning" fontSize="small" />
                  <Typography fontWeight={600} color="error.main">{row.shortage}</Typography>
                </Box>
              ),
            },
          ]}
          data={data}
          loading={loading}
          total={total}
          page={page}
          perPage={20}
          onPageChange={setPage}
          onPerPageChange={() => setPage(1)}
        />
      )}
    </Box>
  );
}