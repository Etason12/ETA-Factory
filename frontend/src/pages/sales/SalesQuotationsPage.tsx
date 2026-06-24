import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, TextField, IconButton, Tooltip, Dialog, DialogTitle, DialogContent,
  DialogContentText, DialogActions, Button, Snackbar, Alert,
} from '@mui/material';
import { Visibility, Edit, Delete, ShoppingCart, Search } from '@mui/icons-material';
import { salesApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { SalesQuotation } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import StatusChip from '../../components/common/StatusChip';
import { formatCurrency, todayStr, monthAgoStr } from '../../utils/format';

export default function SalesQuotationsPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager', 'Sales Officer', 'Sales Manager', 'Branch Manager');
  const canDelete = hasRole('Owner');
  const canConvert = hasRole('Owner', 'General Manager', 'Sales Officer', 'Sales Manager', 'Branch Manager');
  const canCreate = hasRole('Owner', 'General Manager', 'Sales Officer', 'Sales Manager', 'Branch Manager');
  const [quotations, setQuotations] = useState<SalesQuotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [convertId, setConvertId] = useState<number | null>(null);
  const [success, setSuccess] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchQuotations = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (search) params.search = search;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await salesApi.quotations.list(params);
      setQuotations(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load quotations');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, dateFrom, dateTo]);

  useEffect(() => {
    fetchQuotations();
  }, [fetchQuotations]);

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await salesApi.quotations.delete(deleteId);
      setSuccess('Quotation deleted successfully');
      blurActiveElement();
      setDeleteId(null);
      fetchQuotations();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to delete quotation');
    }
  };

  const handleConvert = async () => {
    if (!convertId) return;
    try {
      await salesApi.quotations.convert(convertId);
      setSuccess('Quotation converted to order successfully');
      blurActiveElement();
      setConvertId(null);
      fetchQuotations();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to convert quotation');
    }
  };

  const columns = [
    { id: 'quotation_number', label: 'Quotation #' },
    { id: 'customer_name', label: 'Customer' },
    {
      id: 'status', label: 'Status',
      render: (row: SalesQuotation) => <StatusChip status={row.status} />,
    },
    {
      id: 'total_amount', label: 'Total', nowrap: true,
      render: (row: SalesQuotation) => formatCurrency(row.total_amount),
    },
    {
      id: 'valid_until', label: 'Valid Until',
      render: (row: SalesQuotation) => row.valid_until ? new Date(row.valid_until).toLocaleDateString() : '-',
    },
    {
      id: 'actions', label: 'Actions',
      render: (row: SalesQuotation) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View">
            <IconButton size="small" onClick={() => navigate(`/sales/quotations/${row.id}`)}>
              <Visibility fontSize="small" />
            </IconButton>
          </Tooltip>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" color="primary" onClick={() => navigate(`/sales/quotations/${row.id}/edit`)}>
                <Edit fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {canDelete && (
            <Tooltip title="Delete">
              <IconButton size="small" color="error" onClick={() => setDeleteId(row.id)}>
                <Delete fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status !== 'Converted' && row.status !== 'Cancelled' && canConvert && (
            <Tooltip title="Convert to Order">
              <IconButton size="small" color="success" onClick={() => setConvertId(row.id)}>
                <ShoppingCart fontSize="small" />
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
        title="Sales Quotations"
        subtitle="Manage customer quotations"
        action={canCreate ? { label: 'New Quotation', path: '/sales/quotations/new' } : undefined}
      />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search by quotation # or customer..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          slotProps={{ input: { startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          sx={{ minWidth: 320 }}
        />
        <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={(v) => { setDateFrom(v); setPage(1); }} onDateToChange={(v) => { setDateTo(v); setPage(1); }} />
      </Box>
      <DataTable
        columns={columns}
        data={quotations}
        loading={loading}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={setPerPage}
      />
      <Dialog open={!!deleteId} onClose={() => { blurActiveElement(); setDeleteId(null); }} disableRestoreFocus>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>Are you sure you want to delete this quotation? This action cannot be undone.</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteId(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>Delete</Button>
        </DialogActions>
      </Dialog>
      <Dialog open={!!convertId} onClose={() => { blurActiveElement(); setConvertId(null); }} disableRestoreFocus>
        <DialogTitle>Convert to Order</DialogTitle>
        <DialogContent>
          <DialogContentText>Convert this quotation into a sales order?</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConvertId(null)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleConvert}>Convert</Button>
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
