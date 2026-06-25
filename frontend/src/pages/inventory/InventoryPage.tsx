import { useCallback, useEffect, useState } from 'react';
import {
  Box, TextField, FormControl, InputLabel, Select, MenuItem, Snackbar, Alert,
  Typography,
} from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { inventoryApi, warehousesApi } from '../../api/endpoints';
import type { Inventory, Warehouse } from '../../types';

export default function InventoryPage() {
  const [data, setData] = useState<Inventory[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | ''>('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchWarehouses = useCallback(async () => {
    try {
      const res = await warehousesApi.list({ per_page: 200 });
      setWarehouses(res.items || []);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load warehouses');
    }
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage, grouped: true };
      if (search.trim()) params.search = search.trim();
      if (warehouseId !== '') params.warehouse_id = warehouseId;
      const res = await inventoryApi.list(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load inventory');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, warehouseId]);

  useEffect(() => {
    fetchWarehouses();
  }, [fetchWarehouses]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const columns = [
    { id: 'product_name', label: 'Product' },
    { id: 'product_sku', label: 'SKU' },
    { id: 'warehouse_name', label: 'Warehouse' },
    {
      id: 'quantity_on_hand',
      label: 'On Hand',
      render: (row: Inventory) => {
        const isLow = row.min_stock_level != null && row.min_stock_level > 0 && row.quantity_on_hand <= row.min_stock_level;
        return (
          <Typography color={isLow ? 'error.main' : 'text.primary'} fontWeight={isLow ? 700 : 400}>
            {Number(row.quantity_on_hand).toLocaleString()}
          </Typography>
        );
      },
    },
    {
      id: 'reserved_quantity',
      label: 'Reserved',
      render: (row: Inventory) => Number(row.reserved_quantity).toLocaleString(),
    },
    {
      id: 'available_quantity',
      label: 'Available',
      render: (row: Inventory) => Number(row.available_quantity).toLocaleString(),
    },
    {
      id: 'min_stock_level',
      label: 'Min',
      render: (row: Inventory) => (row.min_stock_level != null && row.min_stock_level > 0 ? row.min_stock_level : '-'),
    },
    {
      id: 'max_stock_level',
      label: 'Max',
      render: (row: Inventory) => (row.max_stock_level != null && row.max_stock_level > 0 ? row.max_stock_level : '-'),
    },
    { id: 'batch_number', label: 'Batch' },
  ];

  return (
    <>
      <PageHeader
        title="Stock Levels"
        subtitle="Current inventory across warehouses — set min/max thresholds in Product settings"
      />
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search product..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          sx={{ width: 320 }}
        />
        <FormControl size="small" sx={{ width: 240 }}>
          <InputLabel>Warehouse</InputLabel>
          <Select
            value={warehouseId}
            label="Warehouse"
            onChange={(e) => { setWarehouseId(e.target.value as number | ''); setPage(1); }}
          >
            <MenuItem value="">All</MenuItem>
            {warehouses.map((w) => (
              <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />

      <Snackbar open={!!errorMsg} autoHideDuration={6000} onClose={() => setErrorMsg('')}>
        <Alert severity="error" onClose={() => setErrorMsg('')}>{errorMsg}</Alert>
      </Snackbar>
    </>
  );
}
