import { useState, useEffect, useCallback } from 'react';
import { Box, TextField, Typography, Snackbar, Alert, Link, IconButton, Tooltip } from '@mui/material';
import { Search, OpenInNew, Print } from '@mui/icons-material';
import { salesApi } from '../../api/endpoints';
import type { Payment } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import { formatCurrency, todayStr, monthAgoStr } from '../../utils/format';
import apiClient from '../../api/client';

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchPayments = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (search) params.search = search;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await salesApi.payments.list(params);
      setPayments(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load payments');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, dateFrom, dateTo]);

  useEffect(() => {
    fetchPayments();
  }, [fetchPayments]);

  const backendOrigin = apiClient.defaults.baseURL?.replace(/\/api\/v1\/?$/, '') || 'http://localhost:5000';

  const handlePrintReceipt = (paymentId: number) => {
    const token = localStorage.getItem('access_token');
    window.open(`/api/v1/sales/payments/${paymentId}/receipt-view?token=${token}`, '_blank');
  };

const columns = [
    { id: 'payment_number', label: 'Payment #' },
    { id: 'invoice_number', label: 'Invoice #' },
    { id: 'customer_name', label: 'Customer' },
    {
      id: 'amount', label: 'Amount', nowrap: true,
      render: (row: Payment) => formatCurrency(row.amount),
    },
    {
      id: 'payment_date', label: 'Payment Date',
      render: (row: Payment) => new Date(row.payment_date).toLocaleDateString(),
    },
    { id: 'payment_method', label: 'Method' },
    { id: 'reference_number', label: 'Reference', render: (row: Payment) => row.reference_number || '-' },
    {
      id: 'bank_name', label: 'Bank Name',
      render: (row: Payment) => row.payment_method === 'Bank Transfer' ? (row.bank_name || '-') : '-',
    },
    {
      id: 'receipt_image', label: 'Receipt',
      render: (row: Payment) => row.receipt_image ? (
        <Link href={`${backendOrigin}${row.receipt_image}`} target="_blank" rel="noopener" underline="none" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
          View <OpenInNew fontSize="small" />
        </Link>
      ) : '-',
    },
    {
      id: 'actions', label: 'Actions', sortable: false, nowrap: true,
      render: (row: Payment) => (
        <Tooltip title="Print Receipt">
          <IconButton size="small" onClick={() => handlePrintReceipt(row.id)} color="primary">
            <Print fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Payments"
        subtitle="View customer payment records"
      />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search by payment #, invoice #, or customer..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          slotProps={{ input: { startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          sx={{ minWidth: 320 }}
        />
        <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={(v) => { setDateFrom(v); setPage(1); }} onDateToChange={(v) => { setDateTo(v); setPage(1); }} />
      </Box>
      {payments.length > 0 && (
        <Box sx={{ mb: 2, display: 'flex', gap: 3, flexWrap: 'wrap', px: 0.5 }}>
          <Typography variant="body2">
            Page Total: <strong>{formatCurrency(payments.reduce((s, p) => s + (p.amount || 0), 0))}</strong>
          </Typography>
        </Box>
      )}
      <DataTable
        columns={columns}
        data={payments}
        loading={loading}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={setPerPage}
      />
      <Snackbar open={!!errorMsg} autoHideDuration={6000} onClose={() => setErrorMsg('')}>
        <Alert severity="error" onClose={() => setErrorMsg('')}>{errorMsg}</Alert>
      </Snackbar>
    </Box>
  );
}
