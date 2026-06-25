import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Card, CardContent, Button, TextField, Autocomplete,
  Grid2 as Grid, Typography, IconButton, Snackbar, Alert, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, InputAdornment, Stepper, Step, StepLabel
} from '@mui/material';
import { Delete } from '@mui/icons-material';
import { salesApi, customersApi, productsApi, branchesApi } from '../../api/endpoints';
import type { Customer, Product, Branch } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import { formatCurrency, getCurrencyCode, todayStr } from '../../utils/format';

interface LineItem {
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
}

const steps = ['Quotation Details', 'Line Items', 'Review & Submit'];

export default function SalesQuotationFormPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;
  
  const [activeStep, setActiveStep] = useState(0);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  
  const [quotationNumber, setQuotationNumber] = useState('');
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [validUntil, setValidUntil] = useState(todayStr);
  const [notes, setNotes] = useState('');
  const [lineItems, setLineItems] = useState<LineItem[]>([{ product_id: 0, product_name: '', quantity: 1, unit_price: 0 }]);
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      customersApi.list({ per_page: 1000 }),
      productsApi.list({ per_page: 1000 }),
      branchesApi.list({ per_page: 1000 }),
    ]).then(([c, p, b]) => {
      setCustomers(c.items || []);
      setProducts(p.items || []);
      setBranches(b.items || []);
    });
    
    if (isEdit) {
      salesApi.quotations.get(Number(id)).then(res => {
        setQuotationNumber(res.quotation_number);
        setCustomerId(res.customer_id);
        setBranchId(res.branch_id);
        setValidUntil(res.valid_until ? res.valid_until.split('T')[0] : todayStr);
        setNotes(res.notes || '');
        if (res.items && res.items.length > 0) {
          setLineItems(res.items.map((i: any) => ({
            product_id: i.product_id,
            product_name: i.product_name || '',
            quantity: i.quantity,
            unit_price: i.unit_price,
          })));
        }
      });
    }
  }, [id, isEdit]);

  const handleNext = () => setActiveStep((s) => s + 1);
  const handleBack = () => setActiveStep((s) => s - 1);
  const addLine = () => setLineItems([...lineItems, { product_id: 0, product_name: '', quantity: 1, unit_price: 0 }]);
  const removeLine = (i: number) => {
    if (lineItems.length > 1) setLineItems(lineItems.filter((_, idx) => idx !== i));
  };

  const handleProductChange = (i: number, product: Product | null) => {
    const items = [...lineItems];
    if (product) {
      items[i] = { ...items[i], product_id: product.id, product_name: product.name, unit_price: product.unit_price };
    } else {
      items[i] = { product_id: 0, product_name: '', unit_price: 0, quantity: 1 };
    }
    setLineItems(items);
  };

  const handleItemChange = (i: number, field: keyof LineItem, value: any) => {
    const items = [...lineItems];
    (items[i] as any)[field] = value;
    setLineItems(items);
  };

  const subtotal = lineItems.reduce((s, item) => s + item.quantity * item.unit_price, 0);

  const valid = () => {
    if (activeStep === 0) return !!quotationNumber && !!customerId && !!branchId && !!validUntil;
    if (activeStep === 1) return lineItems.every((i) => i.product_id > 0 && i.quantity > 0 && i.unit_price >= 0);
    return true;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    const payload = {
      quotation_number: quotationNumber,
      customer_id: customerId,
      branch_id: branchId,
      valid_until: validUntil,
      notes,
      items: lineItems.map((i) => ({ product_id: i.product_id, quantity: i.quantity, unit_price: i.unit_price })),
    };
    
    try {
      if (isEdit) {
        await salesApi.quotations.update(Number(id), payload);
      } else {
        await salesApi.quotations.create(payload);
      }
      navigate('/sales/quotations');
    } catch (err: any) {
      setError(err?.response?.data?.error || err?.response?.data?.detail || 'Failed to save quotation');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <PageHeader title={isEdit ? "Edit Quotation" : "New Quotation"} subtitle="Manage sales quotation details" />
      <Card>
        <CardContent>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
          </Stepper>

          {activeStep === 0 && (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="Quotation Number"
                  value={quotationNumber}
                  onChange={(e) => setQuotationNumber(e.target.value)}
                  required fullWidth
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
              <Grid size={{ xs: 12, md: 6 }}>
                <Autocomplete
                  options={branches}
                  getOptionLabel={(o) => `${o.name} (${o.code})`}
                  value={branches.find((b) => b.id === branchId) || null}
                  onChange={(_, v) => setBranchId(v?.id ?? null)}
                  renderInput={(p) => <TextField {...p} label="Branch" required />}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="Valid Until"
                  type="date"
                  value={validUntil}
                  onChange={(e) => setValidUntil(e.target.value)}
                  required
                  slotProps={{ inputLabel: { shrink: true } }}
                  fullWidth
                />
              </Grid>
              <Grid size={12}>
                <TextField
                  label="Notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  multiline rows={2} fullWidth
                />
              </Grid>
            </Grid>
          )}

          {activeStep === 1 && (
            <Box>
              <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Product</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} width={120}>Quantity</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} width={150}>Unit Price</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} width={120}>Total</TableCell>
                      <TableCell width={50} />
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {lineItems.map((item, i) => (
                      <TableRow key={i}>
                        <TableCell>
                          <Autocomplete
                            options={products}
                            getOptionLabel={(o) => `${o.name} (${o.sku})`}
                            value={products.find((p) => p.id === item.product_id) || null}
                            onChange={(_, v) => handleProductChange(i, v)}
                            renderInput={(p) => <TextField {...p} size="small" placeholder="Select product" />}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small" type="number"
                            value={item.quantity}
                            onChange={(e) => handleItemChange(i, 'quantity', Math.max(1, Number(e.target.value)))}
                            slotProps={{ htmlInput: { min: 1, style: { textAlign: 'right' } } }}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small" type="number"
                            value={item.unit_price}
                            onChange={(e) => handleItemChange(i, 'unit_price', Math.max(0, Number(e.target.value)))}
                            slotProps={{
                              htmlInput: { min: 0, step: 0.01, style: { textAlign: 'right' } },
                              input: { startAdornment: <InputAdornment position="start">{getCurrencyCode()}</InputAdornment> },
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ textAlign: 'right' }}>
                          {formatCurrency(item.quantity * item.unit_price)}
                        </TableCell>
                        <TableCell>
                          <IconButton size="small" color="error" onClick={() => removeLine(i)} disabled={lineItems.length === 1}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Button variant="outlined" onClick={addLine}>Add Product</Button>
            </Box>
          )}

          {activeStep === 2 && (
            <Grid container spacing={4}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>Quotation Details</Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 1, mb: 3 }}>
                  <Typography color="text.secondary">Quotation #:</Typography>
                  <Typography fontWeight={500}>{quotationNumber}</Typography>
                  <Typography color="text.secondary">Customer:</Typography>
                  <Typography fontWeight={500}>{customers.find(c => c.id === customerId)?.name}</Typography>
                  <Typography color="text.secondary">Valid Until:</Typography>
                  <Typography fontWeight={500}>{validUntil}</Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>Summary</Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Subtotal</TableCell>
                        <TableCell align="right">{formatCurrency(subtotal)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>Total</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold' }}>{formatCurrency(subtotal)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button onClick={() => navigate('/sales/quotations')}>Cancel</Button>
            <Box>
              <Button disabled={activeStep === 0} onClick={handleBack} sx={{ mr: 1 }}>Back</Button>
              {activeStep === steps.length - 1 ? (
                <Button variant="contained" onClick={handleSubmit} disabled={submitting || !valid()}>
                  {submitting ? 'Saving...' : 'Save Quotation'}
                </Button>
              ) : (
                <Button variant="contained" onClick={handleNext} disabled={!valid()}>Next</Button>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>
      
      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError('')}>
        <Alert severity="error" onClose={() => setError('')}>{error}</Alert>
      </Snackbar>
    </Box>
  );
}
