import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, TextField, Button, Select, MenuItem, FormControl, InputLabel,
  Switch, FormControlLabel, Alert, CircularProgress, Grid2 as Grid, Typography, Paper,
} from '@mui/material';
import { customersApi, branchesApi } from '../../api/endpoints';
import type { Branch } from '../../types';

interface FormData {
  customer_code: string;
  name: string;
  phone: string;
  email: string;
  address: string;
  tin_number: string;
  customer_type: string;
  credit_limit: number;
  branch_id: number;
  is_active: boolean;
}

const emptyForm = (): FormData => ({
  customer_code: `CUST-${Date.now()}`,
  name: '',
  phone: '',
  email: '',
  address: '',
  tin_number: '',
  customer_type: '',
  credit_limit: 0,
  branch_id: 0,
  is_active: true,
});

export default function CustomerFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState<FormData>(emptyForm());
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const branchRes = await branchesApi.list({ per_page: 500 });
        setBranches(branchRes.items || []);

        if (id) {
          const customer = await customersApi.get(Number(id));
          setForm({
            customer_code: customer.customer_code,
            name: customer.name,
            phone: customer.phone || '',
            email: customer.email || '',
            address: customer.address || '',
            tin_number: customer.tin_number || '',
            customer_type: customer.customer_type,
            credit_limit: customer.credit_limit,
            branch_id: customer.branch_id,
            is_active: customer.is_active,
          });
        }
      } catch (err: any) {
        console.error('Data load error:', err);
        setError(err?.response?.data?.error || err?.response?.data?.detail || 'Failed to load data. Please check your network connection.');
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = { ...form };
      if (id) {
        await customersApi.update(Number(id), payload);
      } else {
        await customersApi.create(payload);
      }
      navigate('/customers');
    } catch (err: any) {
      setError(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to save customer');
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
        {isEdit ? 'Edit Customer' : 'New Customer'}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Paper sx={{ p: 4, maxWidth: 720 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Customer Code" value={form.customer_code} onChange={handleChange('customer_code')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Name" value={form.name} onChange={handleChange('name')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Phone" value={form.phone} onChange={handleChange('phone')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Email" type="email" value={form.email} onChange={handleChange('email')} />
            </Grid>
            <Grid size={12}>
              <TextField fullWidth multiline minRows={2} label="Address" value={form.address} onChange={handleChange('address')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="TIN Number" value={form.tin_number} onChange={handleChange('tin_number')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth required>
                <InputLabel>Customer Type</InputLabel>
                <Select
                  label="Customer Type"
                  value={form.customer_type}
                  onChange={(e) => setForm((prev) => ({ ...prev, customer_type: e.target.value }))}
                >
                  <MenuItem value="individual">Individual</MenuItem>
                  <MenuItem value="business">Business</MenuItem>
                  <MenuItem value="government">Government</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required type="number" label="Credit Limit" value={form.credit_limit} onChange={handleChange('credit_limit')} inputProps={{ min: 0, step: 0.01 }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth required>
                <InputLabel>Branch</InputLabel>
                <Select
                  label="Branch"
                  value={form.branch_id || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, branch_id: e.target.value as number }))}
                >
                  {branches.map((b) => (
                    <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={12}>
              <FormControlLabel
                control={<Switch checked={form.is_active} onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.checked }))} />}
                label="Active"
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
            <Button type="submit" variant="contained" disabled={saving}>
              {saving ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
              {isEdit ? 'Update' : 'Create'}
            </Button>
            <Button variant="outlined" onClick={() => navigate('/customers')}>Cancel</Button>
          </Box>
        </Box>
      </Paper>
    </>
  );
}
