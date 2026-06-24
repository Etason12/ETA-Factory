import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, TextField, Button, MenuItem, Paper, Grid2 as Grid, IconButton,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { transfersApi, productsApi, warehousesApi } from '../../api/endpoints';
import { todayStr } from '../../utils/format';
import type { Product, Warehouse } from '../../types';

interface LineItem {
  product_id: number;
  product_name: string;
  quantity: number;
}

export default function TransferFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [stock, setStock] = useState<Record<number, number>>({});
  const [form, setForm] = useState({
    source_warehouse_id: 0,
    destination_warehouse_id: 0,
    transfer_date: todayStr,
    notes: '',
  });
  const [lineItems, setLineItems] = useState<LineItem[]>([]);

  useEffect(() => {
    Promise.all([
      productsApi.list({ per_page: 1000 }),
      warehousesApi.list({ per_page: 1000 }),
    ]).then(([pRes, wRes]) => {
      setProducts(pRes.items);
      setWarehouses(wRes.items);
    });
  }, []);

  useEffect(() => {
    if (!form.source_warehouse_id) { setStock({}); return; }
    warehousesApi.inventory(form.source_warehouse_id).then((inv: any[]) => {
      const map: Record<number, number> = {};
      inv.forEach((i: any) => {
        map[i.product_id] = (map[i.product_id] || 0) + i.available_quantity;
      });
      setStock(map);
    });
  }, [form.source_warehouse_id]);

  useEffect(() => {
    if (!id) return;
    transfersApi.get(Number(id)).then((t) => {
      setForm({
        source_warehouse_id: t.source_warehouse_id,
        destination_warehouse_id: t.destination_warehouse_id,
        transfer_date: t.transfer_date?.split('T')[0] ?? '',
        notes: t.notes ?? '',
      });
      setLineItems(
        (t.items ?? []).map((i: any) => ({
          product_id: i.product_id,
          product_name: i.product_name ?? '',
          quantity: i.quantity,
        }))
      );
    });
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.source_warehouse_id || !form.destination_warehouse_id) {
      alert('Please select source and destination warehouses');
      return;
    }
    if (form.source_warehouse_id === form.destination_warehouse_id) {
      alert('Source and destination warehouses must be different');
      return;
    }
    if (lineItems.length === 0 || !lineItems.some((l) => l.product_id && l.quantity > 0)) {
      alert('Please add at least one line item');
      return;
    }
    if (isEdit) {
      return;
    }
    setSubmitting(true);
    try {
      await transfersApi.create({
        transfer_number: `TRF-${Date.now()}`,
        ...form,
        items: lineItems
          .filter((l) => l.product_id && l.quantity > 0)
          .map((l) => ({ product_id: l.product_id, quantity: l.quantity })),
      });
      navigate('/transfers');
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to create transfer');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [field]: e.target.value });
  };

  const addLineItem = () => {
    setLineItems([...lineItems, { product_id: 0, product_name: '', quantity: 1 }]);
  };

  const removeLineItem = (idx: number) => {
    setLineItems(lineItems.filter((_, i) => i !== idx));
  };

  const updateLineItem = (idx: number, field: string, value: unknown) => {
    const items = [...lineItems];
    (items[idx] as any)[field] = value;
    if (field === 'product_id') {
      const p = products.find((pr) => pr.id === value);
      if (p) items[idx].product_name = p.name;
    }
    setLineItems(items);
  };

  const destinationWarehouses = warehouses.filter((w) => w.id !== form.source_warehouse_id);

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/transfers')}>
          Back
        </Button>
        <Typography variant="h4">{isEdit ? 'Transfer Details' : 'New Transfer Request'}</Typography>
      </Box>
      <Paper sx={{ p: 3, maxWidth: 800 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2.5}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField label="Source Warehouse *" select fullWidth required
                disabled={isEdit}
                value={form.source_warehouse_id}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setForm({
                    ...form,
                    source_warehouse_id: val,
                    destination_warehouse_id:
                      form.destination_warehouse_id === val ? 0 : form.destination_warehouse_id,
                  });
                }}>
                <MenuItem value={0} disabled>Select source</MenuItem>
                {warehouses.map((w) => (
                  <MenuItem key={w.id} value={w.id}>{w.name} - {w.code}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField label="Destination Warehouse *" select fullWidth required
                disabled={isEdit}
                value={form.destination_warehouse_id}
                onChange={handleChange('destination_warehouse_id')}>
                <MenuItem value={0} disabled>Select destination</MenuItem>
                {destinationWarehouses.map((w) => (
                  <MenuItem key={w.id} value={w.id}>{w.name} - {w.code}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Transfer Date" type="date"
                disabled={isEdit}
                value={form.transfer_date}
                onChange={handleChange('transfer_date')}
                slotProps={{ htmlInput: { max: new Date().toISOString().split('T')[0] } }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Notes" multiline rows={1}
                disabled={isEdit}
                value={form.notes}
                onChange={handleChange('notes')}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Line Items</Typography>
              {lineItems.map((item, idx) => (
                <Box key={idx} sx={{ display: 'flex', gap: 2, mb: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
                  <TextField select label="Product *" size="small" sx={{ flex: 2, minWidth: 180 }}
                    disabled={isEdit}
                    value={item.product_id}
                    onChange={(e) => updateLineItem(idx, 'product_id', Number(e.target.value))}>
                    <MenuItem value={0} disabled>Select product</MenuItem>
                    {products.map((p) => {
                      const avail = stock[p.id] ?? 0;
                      return (
                        <MenuItem key={p.id} value={p.id}>
                          {p.name} ({p.sku}) — Avail: {avail}
                        </MenuItem>
                      );
                    })}
                  </TextField>
                  <TextField label="Quantity *" type="number" size="small" sx={{ flex: 1, minWidth: 100 }}
                    disabled={isEdit}
                    value={item.quantity}
                    onChange={(e) => updateLineItem(idx, 'quantity', Number(e.target.value))}
                    error={item.product_id > 0 && item.quantity > (stock[item.product_id] ?? 0)}
                    helperText={item.product_id > 0 && item.quantity > (stock[item.product_id] ?? 0) ? `Only ${stock[item.product_id] ?? 0} available` : ''}
                    slotProps={{ htmlInput: { min: 1 } }} />
                  {!isEdit && (
                    <IconButton color="error" onClick={() => removeLineItem(idx)}>
                      <DeleteIcon />
                    </IconButton>
                  )}
                </Box>
              ))}
              {!isEdit && (
                <Button size="small" startIcon={<AddIcon />} onClick={addLineItem} sx={{ mt: 1 }}>
                  Add Item
                </Button>
              )}
            </Grid>
            <Grid size={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button variant="outlined" onClick={() => navigate('/transfers')}>
                  {isEdit ? 'Back to Transfers' : 'Cancel'}
                </Button>
                {!isEdit && (
                  <Button type="submit" variant="contained" startIcon={<SaveIcon />} disabled={submitting}>
                    {submitting ? 'Saving...' : 'Create Transfer'}
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </>
  );
}
