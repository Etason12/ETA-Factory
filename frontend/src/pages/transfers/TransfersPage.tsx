import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, IconButton, Tooltip, Dialog, DialogTitle, DialogContent,
  DialogContentText, DialogActions, TextField,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import CancelIcon from '@mui/icons-material/Cancel';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import StatusChip from '../../components/common/StatusChip';
import { transfersApi } from '../../api/endpoints';
import { todayStr, monthAgoStr } from '../../utils/format';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { Transfer } from '../../types';

export default function TransfersPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canApprove = hasRole('Owner', 'General Manager', 'Warehouse Manager');
  const canProcess = hasRole('Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper');
  const canCreate = hasRole('Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper');
  const [data, setData] = useState<Transfer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [confirmAction, setConfirmAction] = useState<{ id: number; action: string; label: string } | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (search.trim()) params.search = search.trim();
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await transfersApi.list(params);
      setData(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, dateFrom, dateTo]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this transfer?')) return;
    try {
      await transfersApi.delete(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.message || 'Failed to delete transfer');
    }
  };

  const handleAction = async () => {
    if (!confirmAction) return;
    try {
      switch (confirmAction.action) {
        case 'approve': await transfersApi.approve(confirmAction.id); break;
        case 'issue': await transfersApi.issue(confirmAction.id); break;
        case 'receive': await transfersApi.receive(confirmAction.id); break;
        case 'cancel': await transfersApi.cancel(confirmAction.id); break;
      }
      blurActiveElement();
      setConfirmAction(null);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || `Failed to ${confirmAction.action} transfer`);
    }
  };

  const columns = [
    { id: 'transfer_number', label: 'Transfer #' },
    { id: 'source_warehouse_name', label: 'Source' },
    { id: 'destination_warehouse_name', label: 'Destination' },
    { id: 'transfer_date', label: 'Date' },
    {
      id: 'status', label: 'Status',
      render: (row: Transfer) => <StatusChip status={row.status} />,
    },
    {
      id: 'actions', label: 'Actions', width: 210,
      render: (row: Transfer) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View">
            <IconButton size="small" onClick={() => navigate(`/transfers/${row.id}/edit`)}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {(row.status === 'Draft' || row.status === 'Pending') && canApprove && (
            <Tooltip title="Approve">
              <IconButton size="small" color="success"
                onClick={() => setConfirmAction({ id: row.id, action: 'approve', label: 'approve' })}>
                <CheckCircleIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Approved' && canProcess && (
            <Tooltip title="Issue Goods">
              <IconButton size="small" color="info"
                onClick={() => setConfirmAction({ id: row.id, action: 'issue', label: 'issue goods for' })}>
                <LocalShippingIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'In Transit' && canProcess && (
            <Tooltip title="Receive">
              <IconButton size="small" color="primary"
                onClick={() => setConfirmAction({ id: row.id, action: 'receive', label: 'receive' })}>
                <DoneAllIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status !== 'Received' && row.status !== 'Cancelled' && canProcess && (
            <Tooltip title="Cancel">
              <IconButton size="small" color="error"
                onClick={() => setConfirmAction({ id: row.id, action: 'cancel', label: 'cancel' })}>
                <CancelIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Draft' && (
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
        title="Transfers"
        subtitle="Manage stock transfers between warehouses"
        action={canCreate ? { label: 'New Transfer', path: '/transfers/new' } : undefined}
      />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small" placeholder="Search transfers..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          sx={{ width: 320 }}
        />
        <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={(v) => { setDateFrom(v); setPage(1); }} onDateToChange={(v) => { setDateTo(v); setPage(1); }} />
      </Box>
      <DataTable
        columns={columns} data={data} loading={loading} total={total}
        page={page} perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />
      <Dialog open={!!confirmAction} onClose={() => setConfirmAction(null)}>
        <DialogTitle>Confirm Action</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to <strong>{confirmAction?.label}</strong> this transfer?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmAction(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleAction}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
