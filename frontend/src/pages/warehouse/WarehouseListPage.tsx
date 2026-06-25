import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  MenuItem, IconButton, Tooltip, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Typography, Paper, Chip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CloseIcon from '@mui/icons-material/Close';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { warehousesApi, branchesApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { Warehouse, Inventory, Branch } from '../../types';

const emptyForm = {
  name: '', code: '', type: 'Warehouse', branch_id: 0, address: '', is_active: true,
};

export default function WarehouseListPage() {
  const [searchParams] = useSearchParams();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager', 'Warehouse Manager');
  const canDelete = hasRole('Owner', 'General Manager', 'Warehouse Manager');
  const canCreate = hasRole('Owner', 'General Manager', 'Warehouse Manager');
  const branchFilter = searchParams.get('branch_id');

  const [data, setData] = useState<Warehouse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [loading, setLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState<Warehouse | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailWarehouse, setDetailWarehouse] = useState<Warehouse | null>(null);
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    branchesApi.list({ per_page: 1000, is_active: 1 }).then((res) => setBranches(res.items || []));
  }, []);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (branchFilter) params.branch_id = Number(branchFilter);
      const res = await warehousesApi.list(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, branchFilter]);

  useEffect(() => { fetch(); }, [fetch]);

  const openCreate = () => {
    setEditingWarehouse(null);
    setForm(emptyForm);
    setFormOpen(true);
  };

  const openEdit = (w: Warehouse) => {
    setEditingWarehouse(w);
    setForm({
      name: w.name,
      code: w.code,
      type: w.type,
      branch_id: w.branch_id,
      address: w.address || '',
      is_active: w.is_active,
    });
    setFormOpen(true);
  };

  const handleViewDetail = async (w: Warehouse) => {
    setDetailWarehouse(w);
    setDetailOpen(true);
    setDetailLoading(true);
    try {
      const inv = await warehousesApi.inventory(w.id);
      setInventory(inv);
    } catch {
      setInventory([]);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.code || !form.branch_id) { alert('Name, code, and branch are required'); return; }
    setSubmitting(true);
    try {
      if (editingWarehouse) {
        await warehousesApi.update(editingWarehouse.id, form);
      } else {
        await warehousesApi.create(form);
      }
      blurActiveElement();
      setFormOpen(false);
      setEditingWarehouse(null);
      setForm(emptyForm);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || (editingWarehouse ? 'Failed to update warehouse' : 'Failed to create warehouse'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this warehouse?')) return;
    try {
      await warehousesApi.delete(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to delete warehouse');
    }
  };

  const columns = [
    { id: 'name', label: 'Name' },
    { id: 'code', label: 'Code' },
    { id: 'type', label: 'Type' },
    { id: 'branch_name', label: 'Branch' },
    { id: 'address', label: 'Address' },
    {
      id: 'is_active', label: 'Status',
      render: (row: Warehouse) => <StatusChip status={row.is_active ? 'Active' : 'Inactive'} />,
    },
    {
      id: 'actions', label: 'Actions', width: 120,
      render: (row: Warehouse) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View Inventory">
            <IconButton size="small" onClick={() => handleViewDetail(row)}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => openEdit(row)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {canDelete && (
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
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4">Warehouses</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Manage warehouse locations and inventory
            {branchFilter && branches.find(b => b.id === Number(branchFilter)) && (
              <> — {branches.find(b => b.id === Number(branchFilter))?.name}</>
            )}
          </Typography>
        </Box>
        {canCreate && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            New Warehouse
          </Button>
        )}
      </Box>
      <DataTable
        columns={columns} data={data} loading={loading} total={total}
        page={page} perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />

      <Dialog open={formOpen} onClose={() => { blurActiveElement(); setFormOpen(false); setEditingWarehouse(null); }} maxWidth="sm" fullWidth disableRestoreFocus>
        <Box component="form" onSubmit={handleSubmit}>
          <DialogTitle>{editingWarehouse ? 'Edit Warehouse' : 'New Warehouse'}</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <TextField label="Name *" fullWidth value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <TextField label="Code *" fullWidth value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value })} />
              <TextField label="Type" select fullWidth value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}>
                <MenuItem value="Warehouse">Warehouse</MenuItem>
                <MenuItem value="Store">Store</MenuItem>
                <MenuItem value="Distribution Center">Distribution Center</MenuItem>
              </TextField>
              <TextField label="Branch *" select fullWidth required value={form.branch_id}
                onChange={(e) => setForm({ ...form, branch_id: Number(e.target.value) })}>
                <MenuItem value={0} disabled>Select a branch</MenuItem>
                {branches.map((b) => (
                  <MenuItem key={b.id} value={b.id}>{b.name} ({b.code})</MenuItem>
                ))}
              </TextField>
              <TextField label="Address" fullWidth multiline rows={2} value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })} />
              <TextField label="Status" select fullWidth value={form.is_active ? 'active' : 'inactive'}
                onChange={(e) => setForm({ ...form, is_active: e.target.value === 'active' })}>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </TextField>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { blurActiveElement(); setFormOpen(false); setEditingWarehouse(null); }}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? 'Saving...' : (editingWarehouse ? 'Update' : 'Save')}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={detailOpen} onClose={() => { blurActiveElement(); setDetailOpen(false); }} maxWidth="md" fullWidth disableRestoreFocus>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{detailWarehouse?.name} - Inventory</span>
          <IconButton size="small" onClick={() => setDetailOpen(false)}><CloseIcon /></IconButton>
        </DialogTitle>
        <DialogContent>
          {detailLoading ? (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>Loading...</Typography>
          ) : inventory.length === 0 ? (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>No inventory records</Typography>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Product</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>SKU</TableCell>
                    <TableCell sx={{ fontWeight: 600 }} align="right">On Hand</TableCell>
                    <TableCell sx={{ fontWeight: 600 }} align="right">Reserved</TableCell>
                    <TableCell sx={{ fontWeight: 600 }} align="right">Available</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {inventory.map((inv) => (
                    <TableRow key={inv.id} hover>
                      <TableCell>{inv.product_name}</TableCell>
                      <TableCell>{inv.product_sku}</TableCell>
                      <TableCell align="right">{inv.quantity_on_hand}</TableCell>
                      <TableCell align="right">{inv.reserved_quantity}</TableCell>
                      <TableCell align="right">
                        <Chip
                          label={inv.available_quantity}
                          size="small"
                          color={inv.available_quantity > 0 ? 'success' : 'error'}
                          variant="outlined"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
