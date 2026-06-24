import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, IconButton, Tooltip, Button, Dialog, DialogTitle, DialogContent,
  DialogContentText, DialogActions, TextField, Snackbar, Alert,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import DeleteIcon from '@mui/icons-material/Delete';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { productionApi, storeApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { ProductionBatch } from '../../types';
import { formatCurrency } from '../../utils/format';

export default function ProductionBatchesPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canApprove = hasRole('Owner', 'General Manager', 'Production Manager');
  const canCancel = hasRole('Owner', 'General Manager', 'Production Manager');
  const canCreate = hasRole('Owner', 'General Manager', 'Production Manager');
  const [data, setData] = useState<ProductionBatch[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [approveTarget, setApproveTarget] = useState<ProductionBatch | null>(null);
  const [snackbar, setSnackbar] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (search.trim()) params.search = search.trim();
      const res = await productionApi.list(params);
      setData(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleApprove = async () => {
    if (!approveTarget) return;
    try {
      await productionApi.approve(approveTarget.id);
      blurActiveElement();
      setApproveTarget(null);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.message || err?.response?.data?.error || 'Failed to approve batch');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this production batch?')) return;
    try {
      await productionApi.delete(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.message || 'Failed to delete batch');
    }
  };

  const handleCreateRequisition = async (batchId: number) => {
    try {
      const res = await storeApi.requisitions.createFromBatch(batchId);
      setSnackbar({ message: res.message || 'Requisition created', severity: 'success' });
      fetch();
    } catch (err: any) {
      setSnackbar({ message: err?.response?.data?.error || 'Failed to create requisition', severity: 'error' });
    }
  };

  const handleCancel = async (id: number) => {
    if (!window.confirm('Cancel this production batch?')) return;
    try {
      await productionApi.cancel(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to cancel batch');
    }
  };

  const columns = [
    { id: 'batch_number', label: 'Batch #' },
    { id: 'product_name', label: 'Product' },
    {
      id: 'quantity_produced', label: 'Quantity',
      render: (row: ProductionBatch) => Number(row.quantity_produced).toLocaleString(),
    },
    {
      id: 'production_cost', label: 'Cost',
      render: (row: ProductionBatch) => formatCurrency(Number(row.production_cost)),
    },
    { id: 'production_date', label: 'Date' },
    { id: 'created_by_name', label: 'Created By' },
    { id: 'approved_by_name', label: 'Approved By' },
    {
      id: 'status', label: 'Status',
      render: (row: ProductionBatch) => <StatusChip status={row.status} />,
    },
    {
      id: 'actions', label: 'Actions', width: 160,
      render: (row: ProductionBatch) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View">
            <IconButton size="small" onClick={() => navigate(`/production/batches/${row.id}/edit`)}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {row.status === 'Pending' && (
            <Tooltip title="Create Store Requisition">
              <IconButton size="small" color="warning" onClick={() => handleCreateRequisition(row.id)}>
                <LocalShippingIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Pending' && canApprove && (
            <Tooltip title="Approve">
              <IconButton size="small" color="success" onClick={() => setApproveTarget(row)}>
                <CheckCircleIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status !== 'Cancelled' && row.status !== 'Completed' && canCancel && (
            <Tooltip title="Cancel">
              <IconButton size="small" color="error" onClick={() => handleCancel(row.id)}>
                <CancelIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Pending' && (
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
        title="Production Batches"
        subtitle="Manage production batch records"
        action={canCreate ? { label: 'New Production Batch', path: '/production/batches/new' } : undefined}
      />
      <TextField
        size="small" placeholder="Search batches..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        sx={{ mb: 2, width: 320 }}
      />
      <DataTable
        columns={columns} data={data} loading={loading} total={total}
        page={page} perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />
      <Dialog open={!!approveTarget} onClose={() => setApproveTarget(null)}>
        <DialogTitle>Confirm Approval</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to approve batch <strong>{approveTarget?.batch_number}</strong>?
            This will update inventory with the produced quantity.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApproveTarget(null)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleApprove}>Approve</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!snackbar}
        autoHideDuration={4000}
        onClose={() => setSnackbar(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar(null)} severity={snackbar?.severity || 'success'} variant="filled">
          {snackbar?.message}
        </Alert>
      </Snackbar>
    </>
  );
}
