import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Box, Button, FormControl, Grid, InputLabel, MenuItem, Select, TextField } from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import { rawMaterialsApi, productsApi } from '../../api/endpoints';
import type { Unit } from '../../types';

interface FormData {
  sku: string;
  name: string;
  description: string;
  cost_price: number;
  unit_id: number;
  is_active: boolean;
  min_stock_level: number;
  max_stock_level: number;
  stock_quantity: number;
}

const emptyForm: FormData = {
  sku: '',
  name: '',
  description: '',
  cost_price: 0,
  unit_id: 0,
  is_active: true,
  min_stock_level: 0,
  max_stock_level: 0,
  stock_quantity: 0,
};

export default function RawMaterialFormPage() {
  const { rawMaterialId } = useParams<{ rawMaterialId: string }>();
  const navigate = useNavigate();
  const isView = window.location.pathname.endsWith('/view');
  const isEdit = !!rawMaterialId && !isView;
  const [form, setForm] = useState<FormData>(emptyForm);
  const [units, setUnits] = useState<Unit[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    productsApi.units().then(setUnits);
  }, []);

  useEffect(() => {
    if (rawMaterialId) {
      rawMaterialsApi.get(Number(rawMaterialId)).then((rm) => {
        setForm({
          sku: rm.sku,
          name: rm.name,
          description: rm.description || '',
          cost_price: rm.cost_price || 0,
          unit_id: rm.unit_id,
          is_active: rm.is_active,
          min_stock_level: rm.min_stock_level || 0,
          max_stock_level: rm.max_stock_level || 0,
          stock_quantity: rm.stock_quantity || 0,
        });
      });
    }
  }, [rawMaterialId]);

  const handleChange = (field: keyof FormData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.unit_id) return;
    setSaving(true);
    try {
      if (isEdit) {
        await rawMaterialsApi.update(Number(rawMaterialId), form);
      } else {
        await rawMaterialsApi.create(form);
      }
      navigate('/raw-materials');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader
        title={isView ? `Raw Material: ${form.name}` : isEdit ? 'Edit Raw Material' : 'New Raw Material'}
        subtitle={isView ? 'View raw material details' : isEdit ? 'Update raw material information' : 'Create a new raw material'}
      />
      <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 800 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="SKU" value={form.sku} onChange={handleChange('sku')} helperText="Leave blank to auto-generate" disabled={isView} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required label="Name" value={form.name} onChange={handleChange('name')} disabled={isView} />
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth multiline rows={3} label="Description" value={form.description} onChange={handleChange('description')} disabled={isView} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required type="number" label="Unit Cost" value={form.cost_price} onChange={handleChange('cost_price')} inputProps={{ min: 0, step: 0.01 }} disabled={isView} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth required disabled={isView}>
              <InputLabel>Unit</InputLabel>
              <Select label="Unit" value={form.unit_id || ''} onChange={(e) => setForm((prev) => ({ ...prev, unit_id: e.target.value as number }))}>
                {units.map((u) => <MenuItem key={u.id} value={u.id}>{u.name} ({u.abbreviation})</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth type="number" label="Current Stock" value={form.stock_quantity} onChange={handleChange('stock_quantity')} inputProps={{ min: 0, step: 0.01 }} helperText="Quantity on hand" disabled={isView} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth type="number" label="Min Stock Level" value={form.min_stock_level} onChange={handleChange('min_stock_level')} inputProps={{ min: 0 }} disabled={isView} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth type="number" label="Max Stock Level" value={form.max_stock_level} onChange={handleChange('max_stock_level')} inputProps={{ min: 0 }} disabled={isView} />
          </Grid>
          {!isView && (
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button type="submit" variant="contained" disabled={saving}>{saving ? 'Saving...' : 'Save'}</Button>
                <Button variant="outlined" onClick={() => navigate('/raw-materials')}>Cancel</Button>
              </Box>
            </Grid>
          )}
        </Grid>
      </Box>
    </>
  );
}
