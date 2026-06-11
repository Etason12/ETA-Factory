import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, TextField, Button, Switch, FormControlLabel, Alert,
  CircularProgress, Grid2 as Grid, Typography, Paper,
} from '@mui/material';
import { branchesApi } from '../../api/endpoints';

interface FormData {
  name: string;
  code: string;
  city: string;
  address: string;
  phone: string;
  email: string;
  is_active: boolean;
}

const emptyForm: FormData = {
  name: '',
  code: '',
  city: '',
  address: '',
  phone: '',
  email: '',
  is_active: true,
};

export default function BranchFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState<FormData>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    branchesApi.get(Number(id))
      .then((res: any) => {
        const b = res?.branch || res;
        setForm({
          name: b.name || '',
          code: b.code || '',
          city: b.city || '',
          address: b.address || '',
          phone: b.phone || '',
          email: b.email || '',
          is_active: b.is_active ?? true,
        });
      })
      .catch((err: any) => setError(`Failed to load branch: ${err.response?.data?.error || err.response?.data?.detail || err.message}`))
      .finally(() => setLoading(false));
  }, [id]);

  const handleChange = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (id) {
        await branchesApi.update(Number(id), form);
      } else {
        await branchesApi.create(form);
      }
      navigate('/branches');
    } catch (err: any) {
      setError(err.response?.data?.error || err.response?.data?.detail || err.message || 'Failed to save branch');
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
        {isEdit ? 'Edit Branch' : 'New Branch'}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 720 }}>
          <Grid container spacing={2.5}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Name" value={form.name} onChange={handleChange('name')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Code" value={form.code} onChange={handleChange('code')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="City" value={form.city} onChange={handleChange('city')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Phone" value={form.phone} onChange={handleChange('phone')} />
            </Grid>
            <Grid size={12}>
              <TextField fullWidth label="Address" value={form.address} onChange={handleChange('address')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Email" type="email" value={form.email} onChange={handleChange('email')} />
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
            <Button variant="outlined" onClick={() => navigate('/branches')}>Cancel</Button>
          </Box>
        </Box>
      </Paper>
    </>
  );
}
