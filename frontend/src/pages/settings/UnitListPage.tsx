import { useCallback, useEffect, useState } from 'react';
import {
  Box, IconButton, Tooltip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, Alert,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { productsApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { Unit } from '../../types';

const emptyForm = { name: '', abbreviation: '' };

export default function UnitListPage() {
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager');

  const [data, setData] = useState<Unit[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [loading, setLoading] = useState(false);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await productsApi.units();
      setData(Array.isArray(res) ? res : []);
      setTotal(Array.isArray(res) ? res.length : 0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleOpenCreate = () => {
    setEditId(null);
    setForm(emptyForm);
    setSaveError('');
    setDialogOpen(true);
  };

  const handleOpenEdit = (row: Unit) => {
    setEditId(row.id);
    setForm({ name: row.name, abbreviation: row.abbreviation });
    setSaveError('');
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.abbreviation.trim()) return;
    setSaving(true);
    setSaveError('');
    try {
      if (editId) {
        await productsApi.updateUnit(editId, form);
      } else {
        await productsApi.createUnit(form);
      }
      blurActiveElement();
      setDialogOpen(false);
      fetchData();
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.response?.data?.message || err?.response?.data?.detail || err?.message || 'Unknown error';
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this unit?')) return;
    try {
      await productsApi.deleteUnit(id);
      fetchData();
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.response?.data?.message || err?.response?.data?.detail || err?.message || 'Failed to delete unit';
      alert(msg);
    }
  };

  const columns = [
    { id: 'name', label: 'Name' },
    { id: 'abbreviation', label: 'Abbreviation' },
    {
      id: 'actions',
      label: 'Actions',
      width: 120,
      render: (row: Unit) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => handleOpenEdit(row)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {canEdit && (
            <Tooltip title="Delete">
              <IconButton size="small" color="error" onClick={() => handleDelete(row.id)}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Units"
        subtitle="Manage units of measure"
        action={canEdit ? { label: 'New Unit', path: '', icon: <AddIcon /> } : undefined}
        onActionClick={handleOpenCreate}
      />
      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />

      <Dialog open={dialogOpen} onClose={() => { setSaveError(''); setDialogOpen(false); }} maxWidth="sm" fullWidth>
        <DialogTitle>{editId ? 'Edit Unit' : 'New Unit'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            {saveError && <Alert severity="error">{saveError}</Alert>}
            <TextField
              label="Name" required fullWidth
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <TextField
              label="Abbreviation" required fullWidth
              value={form.abbreviation}
              onChange={(e) => setForm({ ...form, abbreviation: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving || !form.name.trim() || !form.abbreviation.trim()}>
            {saving ? 'Saving...' : editId ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
