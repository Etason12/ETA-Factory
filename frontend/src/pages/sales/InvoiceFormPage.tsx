import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Card, CardContent, Button, TextField, Autocomplete,
  Grid2 as Grid, Snackbar, Alert, Typography
} from '@mui/material';
import { salesApi, customersApi } from '../../api/endpoints';
import type { Customer, SalesOrder } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import { formatCurrency, todayStr } from '../../utils/format';

export default function InvoiceFormPage() {
  const navigate = useNavigate();
  
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [salesOrders, setSalesOrders] = useState<SalesOrder[]>([]);
  
  const [invoiceNumber, setInvoiceNumber] = useState(`INV-${todayStr.replace(/-/g, '')}-001`);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [salesOrderId, setSalesOrderId] = useState<number | null>(null);
  const [invoiceDate, setInvoiceDate] = useState(todayStr);
  const [dueDate, setDueDate] = useState(todayStr);
  const [notes, setNotes] = useState('');
  
  const [subtotal, setSubtotal] = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      customersApi.list({ per_page: 1000 }),
      salesApi.orders.list({ per_page: 1000, status: 'Approved' }),
    ]).then(([c, s]) => {
      setCustomers(c.items || []);
      setSalesOrders(s.items || []);
    });
  }, []);

  // Auto-populate amounts when a Sales Order is selected
  useEffect(() => {
    if (salesOrderId) {
      const so = salesOrders.find(s => s.id === salesOrderId);
      if (so) {
        if (!customerId) setCustomerId(so.customer_id);
        const sub = Number(so.subtotal) || 0;
        const tot = Number(so.total_amount) || sub;
        setSubtotal(sub);
        setTotalAmount(tot);
      }
    }
  }, [salesOrderId, salesOrders, customerId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoiceNumber || !customerId || !salesOrderId || !invoiceDate || !dueDate) {
      setError('Please fill in all required fields');
      return;
    }
    
    setSubmitting(true);
    setError('');
    
    try {
      await salesApi.invoices.create({
        invoice_number: invoiceNumber,
        sales_order_id: salesOrderId,
        customer_id: customerId,
        invoice_date: invoiceDate,
        due_date: dueDate,
        subtotal,
        total_amount: totalAmount,
        notes,
      });
      navigate('/sales/invoices');
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to create invoice');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <PageHeader title="New Invoice" subtitle="Create a new sales invoice from an order" />
      <Card>
        <CardContent>
          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="Invoice Number"
                  value={invoiceNumber}
                  onChange={(e) => setInvoiceNumber(e.target.value)}
                  required fullWidth
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Autocomplete
                  options={salesOrders}
                  getOptionLabel={(o) => `${o.order_number} (${formatCurrency(o.total_amount)})`}
                  value={salesOrders.find((s) => s.id === salesOrderId) || null}
                  onChange={(_, v) => setSalesOrderId(v?.id ?? null)}
                  renderInput={(p) => <TextField {...p} label="Sales Order" required />}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Autocomplete
                  options={customers}
                  getOptionLabel={(o) => `${o.name} (${o.customer_code})`}
                  value={customers.find((c) => c.id === customerId) || null}
                  onChange={(_, v) => setCustomerId(v?.id ?? null)}
                  renderInput={(p) => <TextField {...p} label="Customer" required />}
                />
              </Grid>
              
              <Grid size={{ xs: 12, md: 3 }}>
                <TextField
                  label="Invoice Date"
                  type="date"
                  value={invoiceDate}
                  onChange={(e) => setInvoiceDate(e.target.value)}
                  required fullWidth
                  slotProps={{ inputLabel: { shrink: true } }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <TextField
                  label="Due Date"
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  required fullWidth
                  slotProps={{ inputLabel: { shrink: true } }}
                />
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="Subtotal"
                  type="number"
                  value={subtotal}
                  onChange={(e) => setSubtotal(Number(e.target.value))}
                  fullWidth
                  slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="Total Amount"
                  type="number"
                  value={totalAmount}
                  onChange={(e) => setTotalAmount(Number(e.target.value))}
                  fullWidth
                  slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
                />
              </Grid>
              
              <Grid size={12}>
                <TextField
                  label="Notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  multiline rows={3} fullWidth
                />
              </Grid>
              
              <Grid size={12}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
                  <Button onClick={() => navigate('/sales/invoices')}>Cancel</Button>
                  <Button type="submit" variant="contained" disabled={submitting}>
                    {submitting ? 'Saving...' : 'Create Invoice'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>
      
      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError('')}>
        <Alert severity="error" onClose={() => setError('')}>{error}</Alert>
      </Snackbar>
    </Box>
  );
}
