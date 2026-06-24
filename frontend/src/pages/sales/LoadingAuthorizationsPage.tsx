import { useState, useEffect, useCallback } from 'react';
import { Box, TextField, Typography, IconButton, Tooltip, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button, Snackbar, Alert } from '@mui/material';
import { CheckCircle, Search } from '@mui/icons-material';
import { salesApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { LoadingAuthorization } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';

export default function LoadingAuthorizationsPage() {
  const { hasRole } = useAuthStore();
  const canApprove = hasRole('Owner', 'General Manager', 'Sales Manager', 'Warehouse Manager');
  const [auths, setAuths] = useState<LoadingAuthorization[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [approveId, setApproveId] = useState<number | null>(null);
  const [success, setSuccess] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchAuths = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res: any = await salesApi.loadingAuthorizations.list(params);
      setAuths(res.loading_authorizations || res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load authorizations');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, statusFilter]);

  useEffect(() => {
    fetchAuths();
  }, [fetchAuths]);

  const handleApprove = async () => {
    if (!approveId) return;
    try {
      await salesApi.loadingAuthorizations.approve(approveId);
      setSuccess('Loading authorization approved successfully');
      blurActiveElement();
      setApproveId(null);
      fetchAuths();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to approve authorization');
    }
  };

  const columns = [
    { id: 'authorization_number', label: 'LA #' },
    { id: 'sales_order_id', label: 'Order ID' },
    { id: 'warehouse_name', label: 'Warehouse' },
    {
      id: 'authorized_date', label: 'Authorized Date',
      render: (row: LoadingAuthorization) => row.authorized_date ? new Date(row.authorized_date).toLocaleDateString() : '—',
    },
    {
      id: 'status', label: 'Status',
      render: (row: LoadingAuthorization) => <StatusChip status={row.status} />,
    },
    { id: 'notes', label: 'Notes' },
    {
      id: 'actions', label: 'Actions',
      render: (row: LoadingAuthorization) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {row.status === 'Pending' && canApprove && (
            <Tooltip title="Approve">
              <IconButton size="small" color="success" onClick={() => setApproveId(row.id)}>
                <CheckCircle fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Loading Authorizations"
        subtitle="Manage goods loading authorizations for sales orders"
      />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search by LA # or order..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          slotProps={{ input: { startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          sx={{ minWidth: 300 }}
        />
        <TextField
          size="small"
          select
          SelectProps={{ native: true }}
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          sx={{ minWidth: 160 }}
        >
          <option value="">All Statuses</option>
          <option value="Pending">Pending</option>
          <option value="Approved">Approved</option>
          <option value="Rejected">Rejected</option>
        </TextField>
      </Box>
      <DataTable
        columns={columns}
        data={auths}
        loading={loading}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={setPerPage}
      />
      <Dialog open={!!approveId} onClose={() => { blurActiveElement(); setApproveId(null); }} disableRestoreFocus>
        <DialogTitle>Confirm Approval</DialogTitle>
        <DialogContent>
          <DialogContentText>Are you sure you want to approve this loading authorization?</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApproveId(null)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleApprove}>Approve</Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={!!success} autoHideDuration={4000} onClose={() => setSuccess('')}>
        <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>
      </Snackbar>
      <Snackbar open={!!errorMsg} autoHideDuration={6000} onClose={() => setErrorMsg('')}>
        <Alert severity="error" onClose={() => setErrorMsg('')}>{errorMsg}</Alert>
      </Snackbar>
    </Box>
  );
}
