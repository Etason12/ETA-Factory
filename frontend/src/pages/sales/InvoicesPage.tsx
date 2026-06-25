import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, TextField, IconButton, Tooltip, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, Snackbar, Alert, MenuItem, Select, InputLabel, FormControl,
  Typography, Grid2 as Grid, Link,
} from '@mui/material';
import { Visibility, Payment, Search, CloudUpload } from '@mui/icons-material';
import { salesApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import type { Invoice } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import StatusChip from '../../components/common/StatusChip';
import { formatCurrency, todayStr, monthAgoStr } from '../../utils/format';

const paymentMethods = ['Cash', 'Bank Transfer', 'Check', 'Mobile Money'];

export default function InvoicesPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canRecordPayment = hasRole('Owner', 'General Manager', 'Sales Manager', 'Accountant');
  const canCreate = hasRole('Owner', 'General Manager', 'Sales Officer', 'Sales Manager');
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [payDialog, setPayDialog] = useState<Invoice | null>(null);
  const [payAmount, setPayAmount] = useState(0);
  const [payDate, setPayDate] = useState(todayStr);
  const [payMethod, setPayMethod] = useState('Cash');
  const [payRef, setPayRef] = useState('');
  const [payBankName, setPayBankName] = useState('');
  const [payReceipt, setPayReceipt] = useState<File | null>(null);
  const [payReceiptPreview, setPayReceiptPreview] = useState('');
  const [payNotes, setPayNotes] = useState('');
  const [paying, setPaying] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [lastPaymentId, setLastPaymentId] = useState<number | null>(null);

  const isBankTransfer = payMethod === 'Bank Transfer';

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (search) params.search = search;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await salesApi.invoices.list(params);
      setInvoices(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, dateFrom, dateTo]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const openPayDialog = (inv: Invoice) => {
    setPayDialog(inv);
    setPayAmount(inv.balance_due);
    setPayDate(todayStr);
    setPayMethod('Cash');
    setPayRef('');
    setPayBankName('');
    setPayReceipt(null);
    setPayReceiptPreview('');
    setPayNotes('');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPayReceipt(file);
      const reader = new FileReader();
      reader.onload = (ev) => setPayReceiptPreview(ev.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  const uploadReceipt = async (): Promise<string | null> => {
    if (!payReceipt) return null;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', payReceipt);
      const res = await fetch('http://localhost:5000/api/v1/sales/upload-receipt', {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: formData,
      });
      const data = await res.json();
      return data.url;
    } catch {
      throw new Error('Failed to upload receipt');
    } finally {
      setUploading(false);
    }
  };

  const handleRecordPayment = async () => {
    if (!payDialog) return;
    setPaying(true);
    setErrorMsg('');
    try {
      let receiptImage = '';
      if (payReceipt) {
        receiptImage = await uploadReceipt() || '';
      }
      const payRes = await salesApi.invoices.pay(payDialog.id, {
        amount: payAmount,
        payment_date: payDate,
        payment_method: payMethod,
        reference_number: isBankTransfer ? payRef : payRef || undefined,
        bank_name: isBankTransfer ? payBankName : undefined,
        receipt_image: receiptImage || undefined,
        notes: payNotes || undefined,
      });
      setLastPaymentId(payRes.payment_id);
      setSuccess('Payment recorded successfully');
      blurActiveElement();
      setPayDialog(null);
      fetchInvoices();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to record payment');
    } finally {
      setPaying(false);
    }
  };

  const [viewDialog, setViewDialog] = useState<Invoice | null>(null);

  const columns = [
    { id: 'invoice_number', label: 'Invoice #' },
    { id: 'customer_name', label: 'Customer' },
    {
      id: 'invoice_date', label: 'Invoice Date',
      render: (row: Invoice) => new Date(row.invoice_date).toLocaleDateString(),
    },
    {
      id: 'total_amount', label: 'Total', nowrap: true,
      render: (row: Invoice) => formatCurrency(row.total_amount),
    },
    {
      id: 'paid_amount', label: 'Paid', nowrap: true,
      render: (row: Invoice) => formatCurrency(row.paid_amount),
    },
    {
      id: 'balance_due', label: 'Balance', nowrap: true,
      render: (row: Invoice) => formatCurrency(row.balance_due),
    },
    {
      id: 'payment_status', label: 'Payment Status',
      render: (row: Invoice) => <StatusChip status={row.payment_status === 'Unpaid' ? 'Unpaid' : row.payment_status === 'Partial' ? 'Partial' : 'Paid'} />,
    },
    {
      id: 'actions', label: 'Actions',
      render: (row: Invoice) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View Details">
            <IconButton size="small" onClick={() => setViewDialog(row)}>
              <Visibility fontSize="small" />
            </IconButton>
          </Tooltip>
          {row.balance_due > 0 && canRecordPayment && (
            <Tooltip title="Record Payment">
              <IconButton size="small" color="success" onClick={() => openPayDialog(row)}>
                <Payment fontSize="small" />
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
        title="Invoices"
        subtitle="Manage customer invoices and payments"
        action={canCreate ? { label: 'New Invoice', path: '/sales/invoices/new' } : undefined}
      />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search by invoice # or customer..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          slotProps={{ input: { startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          sx={{ minWidth: 320 }}
        />
        <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={(v) => { setDateFrom(v); setPage(1); }} onDateToChange={(v) => { setDateTo(v); setPage(1); }} />
      </Box>
      {invoices.length > 0 && (
        <Box sx={{ mb: 2, display: 'flex', gap: 3, flexWrap: 'wrap', px: 0.5 }}>
          <Typography variant="body2">
            Page Total: <strong>{formatCurrency(invoices.reduce((s, i) => s + (i.total_amount || 0), 0))}</strong>
          </Typography>
          <Typography variant="body2">
            Paid: <strong>{formatCurrency(invoices.reduce((s, i) => s + (i.paid_amount || 0), 0))}</strong>
          </Typography>
          <Typography variant="body2">
            Balance: <strong>{formatCurrency(invoices.reduce((s, i) => s + (i.balance_due || 0), 0))}</strong>
          </Typography>
        </Box>
      )}
      <DataTable
        columns={columns}
        data={invoices}
        loading={loading}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={setPerPage}
      />
      <Dialog open={!!payDialog} onClose={() => { blurActiveElement(); setPayDialog(null); }} maxWidth="sm" fullWidth disableRestoreFocus>
        <DialogTitle>Record Payment</DialogTitle>
        <DialogContent>
          {payDialog && (
            <Grid container spacing={2} sx={{ mt: 0.5 }}>
              <Grid size={12}>
                <Typography variant="body2" color="text.secondary">
                  Invoice: {payDialog.invoice_number} | Balance Due: {formatCurrency(payDialog.balance_due)}
                </Typography>
              </Grid>
              <Grid size={6}>
                <TextField
                  label="Amount"
                  type="number"
                  value={payAmount}
                  onChange={(e) => setPayAmount(Math.max(0, Number(e.target.value)))}
                  slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
                  fullWidth
                  required
                />
              </Grid>
              <Grid size={6}>
                <TextField
                  label="Payment Date"
                  type="date"
                  value={payDate}
                  onChange={(e) => setPayDate(e.target.value)}
                  slotProps={{ inputLabel: { shrink: true } }}
                  fullWidth
                  required
                />
              </Grid>
              <Grid size={6}>
                <FormControl fullWidth required>
                  <InputLabel>Payment Method</InputLabel>
                  <Select
                    value={payMethod}
                    label="Payment Method"
                    onChange={(e) => setPayMethod(e.target.value)}
                  >
                    {paymentMethods.map((m) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={6}>
                <TextField
                  label={isBankTransfer ? 'Reference Number *' : 'Reference Number'}
                  value={payRef}
                  onChange={(e) => setPayRef(e.target.value)}
                  fullWidth
                  required={isBankTransfer}
                />
              </Grid>
              {isBankTransfer && (
                <>
                  <Grid size={6}>
                    <TextField
                      label="Bank Name *"
                      value={payBankName}
                      onChange={(e) => setPayBankName(e.target.value)}
                      fullWidth
                      required
                    />
                  </Grid>
                  <Grid size={6}>
                    <Button
                      variant="outlined"
                      component="label"
                      fullWidth
                      startIcon={<CloudUpload />}
                      sx={{ height: 56 }}
                    >
                      {payReceipt ? payReceipt.name : 'Upload Receipt *'}
                      <input type="file" hidden accept="image/*" onChange={handleFileChange} />
                    </Button>
                  </Grid>
                  {payReceiptPreview && (
                    <Grid size={12}>
                      <Box
                        component="img"
                        src={payReceiptPreview}
                        sx={{ maxHeight: 160, borderRadius: 1, border: '1px solid', borderColor: 'divider' }}
                      />
                    </Grid>
                  )}
                </>
              )}
              <Grid size={12}>
                <TextField
                  label="Notes"
                  value={payNotes}
                  onChange={(e) => setPayNotes(e.target.value)}
                  multiline
                  rows={2}
                  fullWidth
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPayDialog(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleRecordPayment} disabled={paying || uploading || payAmount <= 0}>
            {uploading ? 'Uploading...' : paying ? 'Recording...' : 'Record Payment'}
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={!!success} autoHideDuration={6000} onClose={() => setSuccess('')}>
        <Alert
          severity="success"
          onClose={() => setSuccess('')}
          action={lastPaymentId ? (
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                const token = localStorage.getItem('access_token');
                window.open(`/api/v1/sales/payments/${lastPaymentId}/receipt-view?token=${token}`, '_blank');
              }}
            >
              Print Receipt
            </Button>
          ) : undefined}
        >
          {success}
        </Alert>
      </Snackbar>
      <Snackbar open={!!errorMsg} autoHideDuration={6000} onClose={() => setErrorMsg('')}>
        <Alert severity="error" onClose={() => setErrorMsg('')}>{errorMsg}</Alert>
      </Snackbar>
      <Dialog open={!!viewDialog} onClose={() => { blurActiveElement(); setViewDialog(null); }} maxWidth="sm" fullWidth disableRestoreFocus>
        <DialogTitle>Invoice Details</DialogTitle>
        <DialogContent>
          {viewDialog && (
            <Grid container spacing={2} sx={{ mt: 0.5 }}>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Invoice #</Typography>
                <Typography fontWeight={500}>{viewDialog.invoice_number}</Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Customer</Typography>
                <Typography fontWeight={500}>{viewDialog.customer_name}</Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Invoice Date</Typography>
                <Typography>{new Date(viewDialog.invoice_date).toLocaleDateString()}</Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Due Date</Typography>
                <Typography>{viewDialog.due_date ? new Date(viewDialog.due_date).toLocaleDateString() : '-'}</Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Subtotal</Typography>
                <Typography>{formatCurrency(viewDialog.subtotal)}</Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Total</Typography>
                <Typography fontWeight={700}>{formatCurrency(viewDialog.total_amount)}</Typography>
              </Grid>
              <Grid size={4}>
                <Typography variant="caption" color="text.secondary">Paid</Typography>
                <Typography color="success.main">{formatCurrency(viewDialog.paid_amount)}</Typography>
              </Grid>
              <Grid size={4}>
                <Typography variant="caption" color="text.secondary">Balance Due</Typography>
                <Typography color={viewDialog.balance_due > 0 ? 'error.main' : 'success.main'}>
                  {formatCurrency(viewDialog.balance_due)}
                </Typography>
              </Grid>
              <Grid size={4}>
                <Typography variant="caption" color="text.secondary">Status</Typography>
                <Typography><StatusChip status={viewDialog.payment_status} /></Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          {viewDialog && viewDialog.balance_due > 0 && canRecordPayment && (
            <Button variant="contained" color="success" onClick={() => { setViewDialog(null); openPayDialog(viewDialog); }}>
              Record Payment
            </Button>
          )}
          <Button onClick={() => setViewDialog(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
