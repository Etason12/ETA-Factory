import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, TextField, Typography, IconButton, Tooltip, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button, Snackbar, Alert } from '@mui/material';
import { Visibility, CheckCircle, Cancel, Replay, Search, Edit as EditIcon } from '@mui/icons-material';
import { salesApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { SalesOrder } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import StatusChip from '../../components/common/StatusChip';
import { formatCurrency } from '../../utils/format';

export default function SalesOrdersPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canApprove = hasRole('Owner', 'General Manager', 'Sales Manager', 'Branch Manager');
  const canEditCancel = hasRole('Owner', 'General Manager', 'Sales Manager', 'Branch Manager');
  const canCreate = hasRole('Owner', 'General Manager', 'Sales Officer', 'Sales Manager', 'Branch Manager');
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [approveId, setApproveId] = useState<number | null>(null);
  const [cancelId, setCancelId] = useState<number | null>(null);
  const [cancelStatus, setCancelStatus] = useState<string>('');
  const [success, setSuccess] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (search) params.search = search;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await salesApi.orders.list(params);
      setOrders(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, dateFrom, dateTo]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleApprove = async () => {
    if (!approveId) return;
    try {
      await salesApi.orders.approve(approveId);
      setSuccess('Order approved successfully');
      blurActiveElement();
      setApproveId(null);
      fetchOrders();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to approve order');
    }
  };

  const handleCancel = async () => {
    if (!cancelId) return;
    try {
      await salesApi.orders.cancel(cancelId);
      setSuccess('Order cancelled successfully');
      blurActiveElement();
      setCancelId(null);
      fetchOrders();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to cancel order');
    }
  };

  const columns = [
    { id: 'order_number', label: 'Order #' },
    { id: 'customer_name', label: 'Customer' },
    {
      id: 'order_date', label: 'Order Date',
      render: (row: SalesOrder) => new Date(row.order_date).toLocaleDateString(),
    },
    {
      id: 'status', label: 'Status',
      render: (row: SalesOrder) => <StatusChip status={row.status} />,
    },
    {
      id: 'total_amount', label: 'Total', nowrap: true,
      render: (row: SalesOrder) => formatCurrency(row.total_amount),
    },
    {
      id: 'actions', label: 'Actions',
      render: (row: SalesOrder) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View">
            <IconButton size="small" onClick={() => navigate(`/sales/orders/${row.id}`)}>
              <Visibility fontSize="small" />
            </IconButton>
          </Tooltip>
          {row.status === 'Draft' && canApprove && (
            <Tooltip title="Approve">
              <IconButton size="small" color="success" onClick={() => setApproveId(row.id)}>
                <CheckCircle fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Draft' && canEditCancel && (
            <Tooltip title="Edit">
              <IconButton size="small" color="primary" onClick={() => navigate(`/sales/orders/${row.id}/edit`)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Draft' && canEditCancel && (
            <Tooltip title="Cancel">
              <IconButton size="small" color="error" onClick={() => { setCancelId(row.id); setCancelStatus('Draft'); }}>
                <Cancel fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Approved' && canEditCancel && (
            <Tooltip title="Return Stock">
              <IconButton size="small" color="warning" onClick={() => { setCancelId(row.id); setCancelStatus('Approved'); }}>
                <Replay fontSize="small" />
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
        title="Sales Orders"
        subtitle="Manage customer sales orders"
        action={canCreate ? { label: 'New Sales Order', path: '/sales/orders/new' } : undefined}
      />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search by order # or customer..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          slotProps={{ input: { startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          sx={{ minWidth: 320 }}
        />
        <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={(v) => { setDateFrom(v); setPage(1); }} onDateToChange={(v) => { setDateTo(v); setPage(1); }} />
      </Box>
      {orders.length > 0 && (
        <Box sx={{ mb: 2, display: 'flex', gap: 3, flexWrap: 'wrap', px: 0.5 }}>
          <Typography variant="body2">
            Page Total: <strong>{formatCurrency(orders.reduce((s, o) => s + (o.total_amount || 0), 0))}</strong>
          </Typography>
        </Box>
      )}
      <DataTable
        columns={columns}
        data={orders}
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
          <DialogContentText>Are you sure you want to approve this sales order?</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApproveId(null)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleApprove}>Approve</Button>
        </DialogActions>
      </Dialog>
      <Dialog open={!!cancelId} onClose={() => { blurActiveElement(); setCancelId(null); }} disableRestoreFocus>
        <DialogTitle>{cancelStatus === 'Approved' ? 'Confirm Return' : 'Confirm Cancellation'}</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {cancelStatus === 'Approved'
              ? 'This order has already been approved and stock deducted. Cancelling will return all items to inventory. Continue?'
              : 'Are you sure you want to cancel this sales order?'}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelId(null)}>No</Button>
          <Button variant="contained" color="error" onClick={handleCancel}>
            {cancelStatus === 'Approved' ? 'Yes, Return Stock' : 'Yes, Cancel'}
          </Button>
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
