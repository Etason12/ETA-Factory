import { useCallback, useEffect, useState } from 'react';
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  MenuItem, IconButton, Typography, Tooltip, Grid2 as Grid, Chip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckIcon from '@mui/icons-material/Check';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import StatusChip from '../../components/common/StatusChip';
import { warehousesApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import { todayStr, monthAgoStr } from '../../utils/format';
import type { Warehouse } from '../../types';

export default function StockAdjustmentPage() {
  const { hasRole } = useAuthStore();
  const canCreate = hasRole('Owner', 'General Manager', 'Warehouse Manager');
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [formOpen, setFormOpen] = useState(false);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [form, setForm] = useState({
    warehouse_id: 0,
    adjustment_type: 'Addition',
    notes: '',
  });
  const [lineItems, setLineItems] = useState<any[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await warehousesApi.listAdjustments(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, dateFrom, dateTo]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this adjustment?')) return;
    try {
      await warehousesApi.deleteAdjustment(id);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.message || 'Failed to delete');
    }
  };

  const handleApprove = async (id: number) => {
    if (!window.confirm('Approve this adjustment? This will update inventory.')) return;
    try {
      await warehousesApi.approveAdjustment(id);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.message || 'Failed to approve');
    }
  };

  useEffect(() => {
    warehousesApi.list({ per_page: 1000 }).then((res) => setWarehouses(res.items || []));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.warehouse_id || lineItems.length === 0) {
      alert('Warehouse and at least one item are required');
      return;
    }
    setSubmitting(true);
    try {
      await warehousesApi.createAdjustment({
        adjustment_number: `ADJ-${Date.now()}`,
        warehouse_id: form.warehouse_id,
        adjustment_type: form.adjustment_type,
        notes: form.notes,
        items: lineItems.map((item: any) => ({
          product_id: item.product_id,
          current_quantity: item.current_quantity,
          adjusted_quantity: item.adjusted_quantity,
        })),
      });
      blurActiveElement();
      setFormOpen(false);
      setForm({ warehouse_id: 0, adjustment_type: 'Addition', notes: '' });
      setLineItems([]);
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to create adjustment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4">Stock Adjustments</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Record inventory additions, reductions, or write-offs
          </Typography>
        </Box>
        {canCreate && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setFormOpen(true)}>
            New Adjustment
          </Button>
        )}
      </Box>

      <Box sx={{ mb: 2 }}>
        <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={(v) => { setDateFrom(v); setPage(1); }} onDateToChange={(v) => { setDateTo(v); setPage(1); }} />
      </Box>

      <DataTable
        columns={[
          { id: 'adjustment_number', label: 'Number' },
          { id: 'warehouse_name', label: 'Warehouse' },
          { id: 'adjustment_type', label: 'Type' },
          {
            id: 'status', label: 'Status',
            render: (row: any) => <StatusChip status={row.status} />,
          },
          {
            id: 'created_at', label: 'Date',
            render: (row: any) => row.created_at ? new Date(row.created_at).toLocaleDateString() : '-',
          },
          {
            id: 'actions', label: 'Actions', width: 110,
            render: (row: any) => (
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {row.status === 'Draft' && (
                  <>
                    <Tooltip title="Approve">
                      <IconButton size="small" color="success" onClick={() => handleApprove(row.id)}>
                        <CheckIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" color="error" onClick={() => handleDelete(row.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </>
                )}
              </Box>
            ),
          },
        ]}
        data={data} loading={loading} total={total}
        page={page} perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />
      
      <Dialog open={formOpen} onClose={() => { blurActiveElement(); setFormOpen(false); }} maxWidth="md" fullWidth disableRestoreFocus>
        <Box component="form" onSubmit={handleCreate}>
          <DialogTitle>New Stock Adjustment</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ pt: 1 }}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Warehouse *" select fullWidth required 
                    value={form.warehouse_id} onChange={(e) => setForm({...form, warehouse_id: Number(e.target.value)})}>
                  <MenuItem value={0} disabled>Select a warehouse</MenuItem>
                  {warehouses.map(w => <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Type *" select fullWidth required 
                    value={form.adjustment_type} onChange={(e) => setForm({...form, adjustment_type: e.target.value})}>
                  <MenuItem value="Addition">Addition</MenuItem>
                  <MenuItem value="Reduction">Reduction</MenuItem>
                </TextField>
              </Grid>
              <Grid size={12}>
                <TextField label="Notes" fullWidth multiline rows={2} value={form.notes}
                  onChange={(e) => setForm({...form, notes: e.target.value})} />
              </Grid>
              <Grid size={12}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Items</Typography>
                {lineItems.map((item, idx) => (
                  <Box key={idx} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                    <TextField size="small" label="Product ID" type="number" sx={{ width: 120 }}
                      value={item.product_id}
                      onChange={(e) => {
                        const updated = [...lineItems];
                        updated[idx] = { ...updated[idx], product_id: Number(e.target.value) };
                        setLineItems(updated);
                      }} />
                    <TextField size="small" label="Current Qty" type="number" sx={{ width: 110 }}
                      value={item.current_quantity}
                      onChange={(e) => {
                        const updated = [...lineItems];
                        updated[idx] = { ...updated[idx], current_quantity: Number(e.target.value) };
                        setLineItems(updated);
                      }} />
                    <TextField size="small" label="Adjusted Qty" type="number" sx={{ width: 110 }}
                      value={item.adjusted_quantity}
                      onChange={(e) => {
                        const updated = [...lineItems];
                        updated[idx] = { ...updated[idx], adjusted_quantity: Number(e.target.value) };
                        setLineItems(updated);
                      }} />
                    <IconButton size="small" color="error" onClick={() => setLineItems(lineItems.filter((_, i) => i !== idx))}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
                <Button size="small" startIcon={<AddIcon />} onClick={() => setLineItems([...lineItems, { product_id: 0, current_quantity: 0, adjusted_quantity: 0 }])}>
                  Add Item
                </Button>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={submitting}>{submitting ? 'Saving...' : 'Save'}</Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  );
}
