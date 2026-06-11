import { useCallback, useEffect, useState } from 'react';
import {
  Box, Button, TextField, MenuItem, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Typography, IconButton,
  Snackbar, Alert, FormControl, InputLabel, Select,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { inventoryApi, productsApi, warehousesApi } from '../../api/endpoints';
import type { Product, Warehouse } from '../../types';

interface LineItem {
  product_id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  batch_number: string;
  unit_cost: string;
}

export default function OpeningBalancePage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | ''>('');
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [existing, setExisting] = useState<any[]>([]);
  const [loadingExisting, setLoadingExisting] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    Promise.all([
      warehousesApi.list({ per_page: 1000 }),
      productsApi.list({ per_page: 1000 }),
    ]).then(([wRes, pRes]) => {
      setWarehouses(wRes.items);
      setProducts(pRes.items);
    });
  }, []);

  const fetchExisting = useCallback(async () => {
    setLoadingExisting(true);
    try {
      const params: any = { page, per_page: 20 };
      if (warehouseId) params.warehouse_id = warehouseId;
      const res = await inventoryApi.openingBalances.list(params);
      setExisting(res.opening_balances || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.message || 'Failed to load opening balances');
    } finally {
      setLoadingExisting(false);
    }
  }, [page, warehouseId]);

  useEffect(() => { fetchExisting(); }, [fetchExisting]);

  const addLineItem = () => {
    setLineItems([...lineItems, { product_id: 0, product_name: '', product_sku: '', quantity: 0, batch_number: '', unit_cost: '' }]);
  };

  const updateLineItem = (idx: number, field: keyof LineItem, value: any) => {
    const updated = [...lineItems];
    if (field === 'product_id') {
      const product = products.find(p => p.id === value);
      updated[idx] = {
        ...updated[idx],
        product_id: value,
        product_name: product?.name || '',
        product_sku: product?.sku || '',
      };
    } else {
      (updated[idx] as any)[field] = value;
    }
    setLineItems(updated);
  };

  const removeLineItem = (idx: number) => {
    setLineItems(lineItems.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    if (!warehouseId) { setErrorMsg('Please select a warehouse'); return; }
    const validItems = lineItems.filter(i => i.product_id > 0 && i.quantity > 0);
    if (validItems.length === 0) { setErrorMsg('Add at least one product with quantity'); return; }

    setSubmitting(true);
    try {
      await inventoryApi.openingBalances.create(
        validItems.map(i => ({
          product_id: i.product_id,
          warehouse_id: warehouseId,
          quantity: i.quantity,
          batch_number: i.batch_number || undefined,
          unit_cost: i.unit_cost ? Number(i.unit_cost) : undefined,
        }))
      );
      setSuccess('Opening balances recorded successfully');
      setLineItems([]);
      fetchExisting();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to set opening balances');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <PageHeader title="Opening Balances" subtitle="Set initial stock quantities for products" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'flex-end' }}>
        <FormControl size="small" sx={{ width: 250 }}>
          <InputLabel>Warehouse</InputLabel>
          <Select value={warehouseId} label="Warehouse" onChange={(e) => setWarehouseId(e.target.value as number | '')}>
            <MenuItem value="">All</MenuItem>
            {warehouses.map(w => <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>Set Opening Balance</Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 3 }}>
        {lineItems.map((item, idx) => (
          <Box key={idx} sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <TextField select label="Product" size="small" sx={{ flex: 2, minWidth: 200 }}
              value={item.product_id}
              onChange={(e) => updateLineItem(idx, 'product_id', Number(e.target.value))}>
              <MenuItem value={0} disabled>Select product</MenuItem>
              {products.map(p => <MenuItem key={p.id} value={p.id}>{p.name} ({p.sku})</MenuItem>)}
            </TextField>
            <TextField label="Qty" type="number" size="small" sx={{ flex: 1, minWidth: 100 }}
              value={item.quantity} slotProps={{ htmlInput: { min: 0 } }}
              onChange={(e) => updateLineItem(idx, 'quantity', Number(e.target.value))} />
            <TextField label="Batch #" size="small" sx={{ flex: 1, minWidth: 120 }}
              value={item.batch_number}
              onChange={(e) => updateLineItem(idx, 'batch_number', e.target.value)} />
            <TextField label="Unit Cost" type="number" size="small" sx={{ flex: 1, minWidth: 120 }}
              value={item.unit_cost} slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
              onChange={(e) => updateLineItem(idx, 'unit_cost', e.target.value)} />
            <IconButton color="error" onClick={() => removeLineItem(idx)}><DeleteIcon /></IconButton>
          </Box>
        ))}
        <Button size="small" startIcon={<AddIcon />} onClick={addLineItem} sx={{ alignSelf: 'flex-start' }}>
          Add Product
        </Button>
        {lineItems.length > 0 && (
          <Button variant="contained" onClick={handleSubmit} disabled={submitting} sx={{ alignSelf: 'flex-start' }}>
            {submitting ? 'Saving...' : 'Save Opening Balances'}
          </Button>
        )}
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>Recorded Opening Balances</Typography>
      <DataTable
        columns={[
          { id: 'product_name', label: 'Product' },
          { id: 'product_sku', label: 'SKU' },
          { id: 'warehouse_name', label: 'Warehouse' },
          { id: 'quantity', label: 'Quantity' },
          { id: 'unit_cost', label: 'Unit Cost', render: (row: any) => row.unit_cost ? Number(row.unit_cost).toFixed(2) : '-' },
          { id: 'batch_number', label: 'Batch' },
          { id: 'transaction_date', label: 'Date', render: (row: any) => row.transaction_date ? new Date(row.transaction_date).toLocaleDateString() : '-' },
        ]}
        data={existing}
        loading={loadingExisting}
        total={total}
        page={page}
        perPage={20}
        onPageChange={setPage}
        onPerPageChange={() => setPage(1)}
      />
      <Snackbar open={!!success} autoHideDuration={4000} onClose={() => setSuccess('')}>
        <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>
      </Snackbar>
      <Snackbar open={!!errorMsg} autoHideDuration={6000} onClose={() => setErrorMsg('')}>
        <Alert severity="error" onClose={() => setErrorMsg('')}>{errorMsg}</Alert>
      </Snackbar>
    </Box>
  );
}