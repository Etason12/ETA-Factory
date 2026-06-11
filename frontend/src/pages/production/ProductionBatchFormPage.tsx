import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, TextField, Button, MenuItem, Paper, Grid2 as Grid, Autocomplete,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import { productionApi, productsApi, warehousesApi } from '../../api/endpoints';
import type { Product, Warehouse } from '../../types';

export default function ProductionBatchFormPage() {
  const { id } = useParams();
  const isView = Boolean(id);
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    product_id: 0,
    quantity_produced: 0,
    production_cost: 0,
    production_date: new Date().toISOString().split('T')[0],
    warehouse_id: 0,
    notes: '',
    batch_number: `PB-${Date.now()}`,
  });
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

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
    if (!id) return;
    productionApi.get(Number(id)).then((batch: any) => {
      const p = products.find((pr) => pr.id === batch.product_id) ?? null;
      setSelectedProduct(p);
      setForm({
        product_id: batch.product_id,
        quantity_produced: batch.quantity_produced,
        production_cost: batch.production_cost,
        production_date: batch.production_date?.split('T')[0] ?? '',
        warehouse_id: batch.warehouse_id,
        notes: batch.notes ?? '',
        batch_number: batch.batch_number,
      });
    });
  }, [id, products]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isView) return;
    if (!form.product_id || !form.warehouse_id || !form.quantity_produced) {
      alert('Please fill in all required fields');
      return;
    }
    setSubmitting(true);
    try {
      await productionApi.create({
        ...form,
        quantity_produced: Number(form.quantity_produced),
        production_cost: Number(form.production_cost),
      });
      navigate('/production/batches');
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to create production batch');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [field]: e.target.value });
  };

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/production/batches')}>
          Back
        </Button>
        <Typography variant="h4">{isView ? `Batch ${form.batch_number}` : 'New Production Batch'}</Typography>
      </Box>
      <Paper sx={{ p: 3, maxWidth: 720 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2.5}>
            <Grid size={{ xs: 12 }}>
              <Autocomplete
                options={products}
                getOptionLabel={(o) => `${o.name} (${o.sku})`}
                value={selectedProduct}
                disabled={isView}
                onChange={(_, v) => {
                  setSelectedProduct(v);
                  setForm({ ...form, product_id: v?.id || 0 });
                }}
                renderInput={(params) => (
                  <TextField {...params} label="Product *" required />
                )}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Quantity Produced *" type="number"
                disabled={isView}
                value={form.quantity_produced}
                onChange={handleChange('quantity_produced')}
                slotProps={{ htmlInput: { min: 1 } }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Production Cost" type="number"
                disabled={isView}
                value={form.production_cost}
                onChange={handleChange('production_cost')}
                slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Production Date" type="date"
                disabled={isView}
                value={form.production_date}
                onChange={handleChange('production_date')}
                slotProps={{ htmlInput: { max: new Date().toISOString().split('T')[0] } }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Warehouse *" select required
                disabled={isView}
                value={form.warehouse_id}
                onChange={handleChange('warehouse_id')}
              >
                <MenuItem value={0} disabled>Select warehouse</MenuItem>
                {warehouses.map((w) => (
                  <MenuItem key={w.id} value={w.id}>{w.name} - {w.code}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth label="Notes" multiline rows={3}
                disabled={isView}
                value={form.notes}
                onChange={handleChange('notes')}
              />
            </Grid>
            <Grid size={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button variant="outlined" onClick={() => navigate('/production/batches')}>
                  {isView ? 'Back' : 'Cancel'}
                </Button>
                {!isView && (
                  <Button type="submit" variant="contained" startIcon={<SaveIcon />} disabled={submitting}>
                    {submitting ? 'Saving...' : 'Save Batch'}
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
