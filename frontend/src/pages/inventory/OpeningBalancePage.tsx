import { useCallback, useEffect, useState } from 'react';
import {
  Box, Button, TextField, MenuItem, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Typography, IconButton,
  Snackbar, Alert, FormControl, InputLabel, Select, ToggleButtonGroup, ToggleButton,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { inventoryApi, productsApi, warehousesApi, rawMaterialsApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { Product, Warehouse, RawMaterial } from '../../types';

type ProductType = 'finished_goods' | 'raw_materials';

interface LineItem {
  item_id: number;
  item_name: string;
  item_sku: string;
  warehouse_id: number;
  quantity: number;
  unit_cost: string;
}

export default function OpeningBalancePage() {
  const { hasRole } = useAuthStore();
  const canAdjust = hasRole('Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper');
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [rawMaterials, setRawMaterials] = useState<RawMaterial[]>([]);
  const [productType, setProductType] = useState<ProductType>('finished_goods');
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
      warehousesApi.list({ is_active: 1, per_page: 99999 }),
      productsApi.list({ per_page: 99999 }),
      rawMaterialsApi.list({ per_page: 99999 }),
    ]).then(([wRes, pRes, rmRes]) => {
      setWarehouses(wRes.items || []);
      setProducts(pRes.items || []);
      setRawMaterials(rmRes.items || []);
    });
  }, []);

  const fetchExisting = useCallback(async () => {
    setLoadingExisting(true);
    try {
      const params: any = { page, per_page: 25 };
      if (warehouseId) params.warehouse_id = warehouseId;
      let res: any;
      if (productType === 'finished_goods') {
        res = await inventoryApi.openingBalances.list(params);
      } else {
        res = await inventoryApi.openingBalances.listRawMaterials(params);
      }
      setExisting(res.opening_balances || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.message || 'Failed to load opening balances');
    } finally {
      setLoadingExisting(false);
    }
  }, [page, warehouseId, productType]);

  useEffect(() => { fetchExisting(); }, [fetchExisting]);

  const handleTypeChange = (_: any, newType: ProductType | null) => {
    if (newType) {
      setProductType(newType);
      setLineItems([]);
      setPage(1);
    }
  };

  const addLineItem = () => {
    setLineItems([...lineItems, { item_id: 0, item_name: '', item_sku: '', warehouse_id: 0, quantity: 0, unit_cost: '' }]);
  };

  const updateLineItem = (idx: number, field: keyof LineItem, value: any) => {
    const updated = [...lineItems];
    if (field === 'item_id') {
      const items = productType === 'finished_goods' ? products : rawMaterials;
      const item = items.find(p => p.id === value);
      updated[idx] = {
        ...updated[idx],
        item_id: value,
        item_name: item?.name || '',
        item_sku: 'sku' in (item || {}) ? (item as any).sku || '' : '',
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
    const validItems = lineItems.filter(i => i.item_id > 0 && i.quantity > 0 && i.warehouse_id > 0);
    if (validItems.length === 0) { setErrorMsg('Add at least one item with item, warehouse, and quantity'); return; }

    setSubmitting(true);
    try {
      const payload = validItems.map(i => ({
        ...(productType === 'finished_goods' ? { product_id: i.item_id } : { raw_material_id: i.item_id }),
        warehouse_id: i.warehouse_id,
        quantity: i.quantity,
        unit_cost: i.unit_cost ? Number(i.unit_cost) : undefined,
      }));
      if (productType === 'finished_goods') {
        await inventoryApi.openingBalances.create(payload);
      } else {
        await inventoryApi.openingBalances.createRawMaterials(payload);
      }
      setSuccess('Opening balances recorded successfully');
      setLineItems([]);
      fetchExisting();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to set opening balances');
    } finally {
      setSubmitting(false);
    }
  };

  const items = productType === 'finished_goods' ? products : rawMaterials;

  return (
    <Box>
      <PageHeader title="Opening Balances" subtitle="Set initial stock quantities for products and raw materials" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'flex-end' }}>
        <ToggleButtonGroup value={productType} exclusive onChange={handleTypeChange} size="small">
          <ToggleButton value="finished_goods">Finished Goods</ToggleButton>
          <ToggleButton value="raw_materials">Raw Materials</ToggleButton>
        </ToggleButtonGroup>
        <FormControl size="small" sx={{ width: 250 }}>
          <InputLabel>Filter by Warehouse</InputLabel>
          <Select value={warehouseId} label="Filter by Warehouse" onChange={(e) => setWarehouseId(e.target.value as number | '')}>
            <MenuItem value="">All</MenuItem>
            {warehouses.map(w => <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>

      {canAdjust && (
        <>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Set Opening Balance — {productType === 'finished_goods' ? 'Finished Goods' : 'Raw Materials'}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 3 }}>
            {lineItems.map((item, idx) => (
              <Box key={idx} sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField select label={productType === 'finished_goods' ? 'Product' : 'Raw Material'} size="small" sx={{ flex: 2, minWidth: 200 }}
                  value={item.item_id}
                  onChange={(e) => updateLineItem(idx, 'item_id', Number(e.target.value))}>
                  <MenuItem value={0} disabled>Select {productType === 'finished_goods' ? 'product' : 'raw material'}</MenuItem>
                  {(items as any[]).map((p: any) => (
                    <MenuItem key={p.id} value={p.id}>
                      {p.sku ? `${p.name} (${p.sku})` : p.name}
                    </MenuItem>
                  ))}
                </TextField>
                <FormControl size="small" sx={{ minWidth: 160 }} required>
                  <InputLabel>Warehouse</InputLabel>
                  <Select value={item.warehouse_id} label="Warehouse" onChange={(e) => updateLineItem(idx, 'warehouse_id', e.target.value as number)}>
                    <MenuItem value={0} disabled>Select warehouse</MenuItem>
                    {warehouses.map(w => <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>)}
                  </Select>
                </FormControl>
                <TextField label="Qty" type="number" size="small" sx={{ flex: 1, minWidth: 100 }}
                  value={item.quantity} slotProps={{ htmlInput: { min: 0 } }}
                  onChange={(e) => updateLineItem(idx, 'quantity', Number(e.target.value))} />
                <TextField label="Unit Cost" type="number" size="small" sx={{ flex: 1, minWidth: 120 }}
                  value={item.unit_cost} slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
                  onChange={(e) => updateLineItem(idx, 'unit_cost', e.target.value)} />
                <IconButton color="error" onClick={() => removeLineItem(idx)}><DeleteIcon /></IconButton>
              </Box>
            ))}
            <Button size="small" startIcon={<AddIcon />} onClick={addLineItem} sx={{ alignSelf: 'flex-start' }}>
              Add {productType === 'finished_goods' ? 'Product' : 'Raw Material'}
            </Button>
            {lineItems.length > 0 && (
              <Button variant="contained" onClick={handleSubmit} disabled={submitting} sx={{ alignSelf: 'flex-start' }}>
                {submitting ? 'Saving...' : 'Save Opening Balances'}
              </Button>
            )}
          </Box>
        </>
      )}

      <Typography variant="h6" sx={{ mb: 2 }}>Recorded Opening Balances</Typography>
      <DataTable
        columns={
          productType === 'finished_goods'
            ? [
                { id: 'product_name', label: 'Product' },
                { id: 'product_sku', label: 'SKU' },
                { id: 'warehouse_name', label: 'Warehouse' },
                { id: 'quantity', label: 'Quantity' },
                { id: 'unit_cost', label: 'Unit Cost', render: (row: any) => row.unit_cost ? Number(row.unit_cost).toFixed(2) : '-' },
                { id: 'transaction_date', label: 'Date', render: (row: any) => row.transaction_date ? new Date(row.transaction_date).toLocaleDateString() : '-' },
              ]
            : [
                { id: 'raw_material_name', label: 'Raw Material' },
                { id: 'raw_material_sku', label: 'SKU' },
                { id: 'warehouse_name', label: 'Warehouse' },
                { id: 'quantity', label: 'Quantity' },
                { id: 'unit_cost', label: 'Unit Cost', render: (row: any) => row.unit_cost ? Number(row.unit_cost).toFixed(2) : '-' },
                { id: 'transaction_date', label: 'Date', render: (row: any) => row.transaction_date ? new Date(row.transaction_date).toLocaleDateString() : '-' },
              ]
        }
        data={existing}
        loading={loadingExisting}
        total={total}
        page={page}
        perPage={25}
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
