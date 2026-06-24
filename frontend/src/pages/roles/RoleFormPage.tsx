import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, TextField, Button, Paper, Typography, Alert, CircularProgress, Grid2 as Grid,
} from '@mui/material';
import { rolesApi } from '../../api/endpoints';
import PageHeader from '../../components/common/PageHeader';

export default function RoleFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    rolesApi.get(Number(id)).then((r) => {
      setName(r.name);
      setDescription(r.description || '');
    }).catch((err: any) => {
      setError(err?.response?.data?.error || 'Failed to load role');
    }).finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('Role name is required'); return; }
    setSaving(true);
    setError('');
    try {
      if (isEdit) {
        await rolesApi.update(Number(id), { name: name.trim(), description: description.trim() });
      } else {
        await rolesApi.create({ name: name.trim(), description: description.trim() });
      }
      navigate('/roles');
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to save role');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  }

  return (
    <Box>
      <PageHeader title={isEdit ? 'Edit Role' : 'New Role'} subtitle={isEdit ? 'Update role details' : 'Create a new role'} />
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      <Paper sx={{ p: 4, maxWidth: 600 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid size={12}>
              <TextField fullWidth required label="Role Name" value={name} onChange={(e) => setName(e.target.value)} />
            </Grid>
            <Grid size={12}>
              <TextField fullWidth label="Description" value={description} onChange={(e) => setDescription(e.target.value)} multiline rows={3} />
            </Grid>
            <Grid size={12} sx={{ display: 'flex', gap: 2 }}>
              <Button variant="contained" type="submit" disabled={saving}>
                {saving ? 'Saving...' : isEdit ? 'Update Role' : 'Create Role'}
              </Button>
              <Button variant="outlined" onClick={() => navigate('/roles')}>Cancel</Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Box>
  );
}
