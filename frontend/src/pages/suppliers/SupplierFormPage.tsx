import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, TextField, Button, Paper, Grid2 as Grid, Switch, FormControlLabel,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import { suppliersApi } from '../../api/endpoints';

export default function SupplierFormPage() {
  const { id } = useParams();
  const isView = window.location.pathname.endsWith('/view');
  const isEdit = Boolean(id) && !isView;
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    code: '', name: '', contact_person: '', phone: '', email: '',
    address: '', payment_terms: '', is_active: true,
  });

  useEffect(() => {
    if (!id) return;
    suppliersApi.get(Number(id)).then((s: any) => {
      setForm({
        code: s.code || '',
        name: s.name || '',
        contact_person: s.contact_person || '',
        phone: s.phone || '',
        email: s.email || '',
        address: s.address || '',
        payment_terms: s.payment_terms || '',
        is_active: s.is_active !== false,
      });
    });
  }, [id]);

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [field]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name) { alert('Name is required'); return; }
    setSubmitting(true);
    try {
      if (isEdit) {
        await suppliersApi.update(Number(id), form);
      } else {
        await suppliersApi.create(form);
      }
      navigate('/suppliers');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to save');
    } finally {
      setSubmitting(false);
    }
  };

  const fields = [
    { label: 'Code', field: 'code', required: false },
    { label: 'Name', field: 'name', required: true },
    { label: 'Contact Person', field: 'contact_person' },
    { label: 'Phone', field: 'phone' },
    { label: 'Email', field: 'email' },
    { label: 'Address', field: 'address', multiline: true },
    { label: 'Payment Terms', field: 'payment_terms' },
  ];

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/suppliers')}>Back</Button>
        <Typography variant="h4">{isEdit ? 'Edit Supplier' : isView ? 'View Supplier' : 'New Supplier'}</Typography>
      </Box>
      <Paper sx={{ p: 3, maxWidth: 720 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2.5}>
            {fields.map((f) => (
              <Grid key={f.field} size={{ xs: 12, sm: f.field === 'address' ? 12 : 6 }}>
                <TextField
                  fullWidth label={f.label} required={f.required}
                  disabled={isView}
                  value={(form as any)[f.field]}
                  onChange={handleChange(f.field)}
                  multiline={f.multiline} rows={f.multiline ? 3 : undefined}
                />
              </Grid>
            ))}
            <Grid size={12}>
              <FormControlLabel
                control={<Switch checked={form.is_active} disabled={isView} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />}
                label="Active"
              />
            </Grid>
            {!isView && (
              <Grid size={12}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                  <Button variant="outlined" onClick={() => navigate('/suppliers')}>Cancel</Button>
                  <Button type="submit" variant="contained" startIcon={<SaveIcon />} disabled={submitting}>
                    {submitting ? 'Saving...' : 'Save'}
                  </Button>
                </Box>
              </Grid>
            )}
          </Grid>
        </Box>
      </Paper>
    </>
  );
}
