import { useEffect, useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import {
  Box, TextField, Button, Select, MenuItem, FormControl, InputLabel,
  Switch, FormControlLabel, Alert, CircularProgress, Grid2 as Grid, Typography, Paper,
} from '@mui/material';
import { productsApi } from '../../api/endpoints';
import type { ProductCategory, Unit } from '../../types';

interface FormData {
  sku: string;
  name: string;
  description: string;
  unit_price: number;
  cost_price: number;
  category_id: number;
  unit_id: number;
  is_active: boolean;
  min_stock_level: number;
  max_stock_level: number;
}

const emptyForm: FormData = {
  sku: '',
  name: '',
  description: '',
  unit_price: 0,
  cost_price: 0,
  category_id: 0,
  unit_id: 0,
  is_active: true,
  min_stock_level: 0,
  max_stock_level: 0,
};

export default function ProductFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const isEdit = Boolean(id);
  const isView = location.pathname.endsWith('/view');

  const [form, setForm] = useState<FormData>(emptyForm);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    const init = async () => {
      try {
        const [catRes, unitRes] = await Promise.all([
          productsApi.categories(),
          productsApi.units(),
        ]);
        setCategories(catRes);
        setUnits(unitRes);

        if (id) {
          const product = await productsApi.get(Number(id));
          setForm({
            sku: product.sku,
            name: product.name,
            description: product.description || '',
            unit_price: product.unit_price,
            cost_price: product.cost_price,
            category_id: product.category_id,
            unit_id: product.unit_id,
            is_active: product.is_active,
            min_stock_level: product.min_stock_level || 0,
            max_stock_level: product.max_stock_level || 0,
          });
        }
      } catch (err: any) {
        console.error('Data load error details:', err.response?.data || err.message);
        setError(`Failed to load data: ${err.response?.data?.error || err.response?.data?.detail || err.message || 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [id]);

  const handleChange = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { value: unknown } },
  ) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent, continueAdding = false) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = { ...form };
      if (id) {
        await productsApi.update(Number(id), payload);
        navigate('/products');
      } else {
        await productsApi.create(payload);
        if (continueAdding) {
            setForm(emptyForm);
        } else {
            navigate('/products');
        }
      }
    } catch (err: any) {
      setError(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to save product');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <Typography variant="h4" sx={{ mb: 3 }}>
        {isView ? 'View Product' : isEdit ? 'Edit Product' : 'New Product'}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={(e) => handleSubmit(e, false)} sx={{ maxWidth: 720 }}>
          <Grid container spacing={2.5}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="SKU" value={form.sku} onChange={handleChange('sku')} disabled={isView} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Name" value={form.name} onChange={handleChange('name')} disabled={isView} />
            </Grid>
            <Grid size={12}>
              <TextField fullWidth multiline minRows={2} label="Description" value={form.description} onChange={handleChange('description')} disabled={isView} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required type="number" label="Unit Price" value={form.unit_price} onChange={handleChange('unit_price')} inputProps={{ min: 0, step: 0.01 }} disabled={isView} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required type="number" label="Cost Price" value={form.cost_price} onChange={handleChange('cost_price')} inputProps={{ min: 0, step: 0.01 }} disabled={isView} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth type="number" label="Min Stock Level" value={form.min_stock_level} onChange={handleChange('min_stock_level')} inputProps={{ min: 0 }} helperText="Items at or below this trigger low-stock alerts" disabled={isView} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth type="number" label="Max Stock Level" value={form.max_stock_level} onChange={handleChange('max_stock_level')} inputProps={{ min: 0 }} helperText="Optional upper limit for reorder planning" disabled={isView} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth required disabled={isView}>
                <InputLabel>Category</InputLabel>
                <Select
                  label="Category"
                  value={form.category_id || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, category_id: e.target.value as number }))}
                >
                  {categories.map((cat) => (
                    <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth required disabled={isView}>
                <InputLabel>Unit</InputLabel>
                <Select
                  label="Unit"
                  value={form.unit_id || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, unit_id: e.target.value as number }))}
                >
                  {units.map((u) => (
                    <MenuItem key={u.id} value={u.id}>{u.name} ({u.abbreviation})</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={12}>
              <FormControlLabel
                control={<Switch checked={form.is_active} onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.checked }))} disabled={isView} />}
                label="Active"
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
            {isView ? (
              <Button variant="outlined" onClick={() => navigate('/products')}>Back to Products</Button>
            ) : (
              <>
                <Button type="submit" variant="contained" disabled={saving}>
                  {saving ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
                  {isEdit ? 'Update' : 'Create'}
                </Button>
                {!isEdit && (
                    <Button type="button" variant="contained" color="secondary" disabled={saving} onClick={(e) => handleSubmit(e, true)}>
                        {saving ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
                        Save & Add Another
                    </Button>
                )}
                <Button variant="outlined" onClick={() => navigate('/products')}>Cancel</Button>
              </>
            )}
          </Box>
        </Box>
      </Paper>
    </>
  );
}
