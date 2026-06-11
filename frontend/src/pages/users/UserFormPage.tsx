import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, TextField, Button, Select, MenuItem, FormControl, InputLabel,
  Switch, FormControlLabel, Alert, CircularProgress, Grid2 as Grid, Typography, Paper,
} from '@mui/material';
import { usersApi, branchesApi } from '../../api/endpoints';
import apiClient from '../../api/client';
import type { Role, Branch } from '../../types';

interface FormData {
  username: string;
  email: string;
  password: string;
  full_name: string;
  phone: string;
  role_id: number;
  branch_id: number;
  is_active: boolean;
}

const emptyForm: FormData = {
  username: '',
  email: '',
  password: '',
  full_name: '',
  phone: '',
  role_id: 0,
  branch_id: 0,
  is_active: true,
};

export default function UserFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState<FormData>(emptyForm);
  const [roles, setRoles] = useState<Role[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [rolesRes, branchesRes] = await Promise.all([
          apiClient.get<Role[]>('/roles'),
          branchesApi.list({ per_page: 200 }),
        ]);
        setRoles(rolesRes.data);
        setBranches(branchesRes.items);

        if (id) {
          const user = await usersApi.get(Number(id));
          setForm({
            username: user.username,
            email: user.email,
            password: '',
            full_name: user.full_name,
            phone: user.phone || '',
            role_id: user.role_id,
            branch_id: user.branch_id || 0,
            is_active: user.is_active,
          });
        }
      } catch (err: any) {
        setError(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load data');
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
      const payload: Record<string, unknown> = { ...form };
      if (isEdit) {
        delete payload.password;
        await usersApi.update(Number(id), payload);
      } else {
        await usersApi.create(payload);
      }
      navigate('/users');
    } catch (err: any) {
      setError(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to save user');
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
        {isEdit ? 'Edit User' : 'New User'}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Paper sx={{ p: 4, maxWidth: 720 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Username" value={form.username} onChange={handleChange('username')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Email" type="email" value={form.email} onChange={handleChange('email')} />
            </Grid>
            {!isEdit && (
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField fullWidth required label="Password" type="password" value={form.password} onChange={handleChange('password')} />
              </Grid>
            )}
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth required label="Full Name" value={form.full_name} onChange={handleChange('full_name')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Phone" value={form.phone} onChange={handleChange('phone')} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth required>
                <InputLabel>Role</InputLabel>
                <Select
                  label="Role"
                  value={form.role_id || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, role_id: e.target.value as number }))}
                >
                  {roles.map((r) => (
                    <MenuItem key={r.id} value={r.id}>{r.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Branch</InputLabel>
                <Select
                  label="Branch"
                  value={form.branch_id || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, branch_id: e.target.value as number }))}
                >
                  <MenuItem value="">None</MenuItem>
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
            <Button variant="outlined" onClick={() => navigate('/users')}>Cancel</Button>
          </Box>
        </Box>
      </Paper>
    </>
  );
}
