import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Card, CardContent, Stepper, Step, StepLabel, Button, TextField, Autocomplete,
  Grid2 as Grid, Typography, IconButton, Alert, Snackbar, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, InputAdornment,
} from '@mui/material';
import { Add, Delete } from '@mui/icons-material';
import { salesApi, customersApi, productsApi, warehousesApi, branchesApi, inventoryApi } from '../../api/endpoints';
import type { Customer, Product, Warehouse, Branch } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import { formatCurrency, getCurrencyCode, todayStr } from '../../utils/format';

interface LineItem {
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
}

interface StockInfo {
  quantity_on_hand: number;
  reserved_quantity: number;
  available_quantity: number;
}

const isReadOnly = (status: string) => ['Approved', 'Completed', 'Cancelled'].includes(status);

const steps = ['Order Details', 'Line Items', 'Review & Submit'];

export default function SalesOrderFormPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;
  const [activeStep, setActiveStep] = useState(0);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [warehouseId, setWarehouseId] = useState<number | null>(null);
  const [orderDate, setOrderDate] = useState(todayStr);
  const [orderNumber, setOrderNumber] = useState('');
  const [lineItems, setLineItems] = useState<LineItem[]>([{ product_id: 0, product_name: '', quantity: 1, unit_price: 0 }]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [readOnly, setReadOnly] = useState(false);
  const [stockMap, setStockMap] = useState<Record<number, StockInfo>>({});

  useEffect(() => {
    Promise.all([
      customersApi.list({ per_page: 1000 }),
      productsApi.list({ per_page: 1000 }),
      warehousesApi.list({ per_page: 1000 }),
      branchesApi.list({ per_page: 1000 }),
    ]).then(([c, p, w, b]) => {
      setCustomers(c.items || []);
      setProducts(p.items || []);
      setWarehouses(w.items || []);
      setBranches(b.items || []);
    });

    if (isEdit) {
      salesApi.orders.get(Number(id)).then(order => {
        setOrderNumber(order.order_number || '');
        setCustomerId(order.customer_id);
        setBranchId(order.branch_id);
        setWarehouseId(order.warehouse_id);
        setOrderDate(order.order_date ? order.order_date.split('T')[0] : todayStr);
        setReadOnly(isReadOnly(order.status));
        if (order.items && order.items.length > 0) {
          setLineItems(order.items.map((i: any) => ({
            product_id: i.product_id,
            product_name: i.product_name || '',
            quantity: i.quantity,
            unit_price: i.unit_price,
          })));
        }
      });
    }
  }, [id, isEdit]);

  const fetchStock = useCallback(async (whId: number) => {
    try {
      const res = await inventoryApi.list({ warehouse_id: whId, per_page: 5000 });
      const map: Record<number, StockInfo> = {};
      for (const inv of (res.items || [])) {
        map[inv.product_id] = {
          quantity_on_hand: Number(inv.quantity_on_hand),
          reserved_quantity: Number(inv.reserved_quantity),
          available_quantity: Number(inv.available_quantity),
        };
      }
      setStockMap(map);
    } catch {
      setStockMap({});
    }
  }, []);

  useEffect(() => {
    if (warehouseId) fetchStock(warehouseId);
    else setStockMap({});
  }, [warehouseId, fetchStock]);

  const handleNext = () => setActiveStep((s) => s + 1);
  const handleBack = () => setActiveStep((s) => s - 1);

  const addLine = () => setLineItems([...lineItems, { product_id: 0, product_name: '', quantity: 1, unit_price: 0 }]);
  const removeLine = (i: number) => {
    setLineItems((prev) => prev.filter((_, idx) => idx !== i));
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
    if (activeStep === 0) return !!customerId && !!branchId && !!warehouseId && !!orderDate;
    if (activeStep === 1) {
      if (!warehouseId) return false;
      return lineItems.every((i) => {
        if (i.product_id <= 0 || i.quantity <= 0 || i.unit_price <= 0) return false;
        const stock = stockMap[i.product_id];
        if (!stock || stock.available_quantity < i.quantity) return false;
        return true;
      });
    }
    return true;
  };

  const handleSubmit = async () => {
    const overStockItem = lineItems.find((i) => {
      const stock = stockMap[i.product_id];
      return !stock || stock.available_quantity < i.quantity;
    });
    if (overStockItem) {
      const avail = stockMap[overStockItem.product_id]?.available_quantity ?? 0;
      setError(`Insufficient stock for "${overStockItem.product_name || overStockItem.product_id}". Available: ${avail}, ordered: ${overStockItem.quantity}`);
      setSubmitting(false);
      return;
    }
    setSubmitting(true);
    setError('');
    const payload = {
      order_number: orderNumber || `ORD-${Date.now()}`,
      customer_id: customerId,
      branch_id: branchId,
      warehouse_id: warehouseId,
      order_date: orderDate,
      items: lineItems.map((i) => ({ product_id: i.product_id, quantity: i.quantity, unit_price: i.unit_price })),
      subtotal,
      total_amount: subtotal,
    };
    try {
      if (isEdit && id) {
        await salesApi.orders.update(Number(id), payload);
        navigate('/sales/orders');
      } else {
        await salesApi.orders.create(payload);
        navigate('/sales/orders');
      }
    } catch (err: any) {
      setError(err?.response?.data?.error || err?.response?.data?.message || 'Failed to save sales order');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedCustomer = customers.find((c) => c.id === customerId);

  const getStock = (productId: number) => stockMap[productId];

  const filteredWarehouses = branchId
    ? warehouses.filter((w) => w.branch_id === branchId)
    : warehouses;

  const handleBranchChange = (branch: Branch | null) => {
    setBranchId(branch?.id ?? null);
    if (warehouseId && branch) {
      const wh = warehouses.find((w) => w.id === warehouseId);
      if (wh && wh.branch_id !== branch.id) {
        setWarehouseId(null);
      }
    }
  };

  const handleWarehouseChange = (warehouse: Warehouse | null) => {
    setWarehouseId(warehouse?.id ?? null);
    if (warehouse && warehouse.branch_id) {
      setBranchId(warehouse.branch_id);
    }
  };

  return (
    <Box>
      <PageHeader title={isEdit ? 'View Sales Order' : 'New Sales Order'} subtitle={isEdit ? 'Review order details' : 'Create a new customer sales order'} />
      <Card>
        <CardContent>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
          </Stepper>

          {activeStep === 0 && (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Autocomplete
                  options={customers}
                  getOptionLabel={(o) => `${o.name} (${o.customer_code})`}
                  value={selectedCustomer || null}
                  onChange={(_, v) => setCustomerId(v?.id ?? null)}
                  renderInput={(p) => <TextField {...p} label="Customer" required />}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Autocomplete
                  options={branches}
                  getOptionLabel={(o) => o.name}
                  value={branches.find((b) => b.id === branchId) || null}
                  onChange={(_, v) => handleBranchChange(v)}
                  renderInput={(p) => <TextField {...p} label="Branch" required />}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Autocomplete
                  options={filteredWarehouses}
                  getOptionLabel={(o) => `${o.name} (${o.code})`}
                  value={warehouses.find((w) => w.id === warehouseId) || null}
                  onChange={(_, v) => handleWarehouseChange(v)}
                  renderInput={(p) => <TextField {...p} label="Warehouse" required />}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  label="Order Date"
                  type="date"
                  value={orderDate}
                  onChange={(e) => setOrderDate(e.target.value)}
                  required
                  slotProps={{ inputLabel: { shrink: true } }}
                  fullWidth
                />
              </Grid>
            </Grid>
          )}

          {activeStep === 1 && (
            <Box>
              {!warehouseId && (
                <Alert severity="info" sx={{ mb: 2 }}>Please select a warehouse in Order Details step to see stock availability.</Alert>
              )}
              <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Product</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} width={80}>Available</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} width={100}>Quantity</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} width={140}>Unit Price</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} width={100}>Total</TableCell>
                      <TableCell width={50} />
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {lineItems.map((item, i) => {
                      const stock = getStock(item.product_id);
                      const noStock = item.product_id > 0 && !stock;
                      const overStock = stock && item.quantity > stock.available_quantity;
                      return (
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
                            {stock != null ? (
                              <Typography
                                variant="body2"
                                color={stock.available_quantity <= 0 ? 'error.main' : 'success.main'}
                                fontWeight={600}
                              >
                                {stock.available_quantity.toLocaleString()}
                              </Typography>
                            ) : noStock ? (
                              <Typography variant="body2" color="error.main" fontWeight={600}>0</Typography>
                            ) : null}
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              type="number"
                              value={item.quantity}
                              onChange={(e) => handleItemChange(i, 'quantity', Math.max(1, Number(e.target.value)))}
                              slotProps={{ htmlInput: { min: 1, style: { textAlign: 'right' } } }}
                              error={overStock || noStock}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              type="number"
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
                            <IconButton size="small" color="error" onClick={() => removeLine(i)}>
                              <Delete fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
              <Button startIcon={<Add />} onClick={addLine}>Add Line Item</Button>
            </Box>
          )}

          {activeStep === 2 && (
            <Box>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" color="text.secondary">Customer</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedCustomer?.name || '-'}</Typography>
                  <Typography variant="subtitle2" color="text.secondary">Branch</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{branches.find((b) => b.id === branchId)?.name || '-'}</Typography>
                  <Typography variant="subtitle2" color="text.secondary">Warehouse</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{warehouses.find((w) => w.id === warehouseId)?.name || '-'}</Typography>
                  <Typography variant="subtitle2" color="text.secondary">Order Date</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{new Date(orderDate).toLocaleDateString()}</Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 600 }}>Product</TableCell>
                          <TableCell sx={{ fontWeight: 600 }} align="right">Avail</TableCell>
                          <TableCell sx={{ fontWeight: 600 }} align="right">Qty</TableCell>
                          <TableCell sx={{ fontWeight: 600 }} align="right">Price</TableCell>
                          <TableCell sx={{ fontWeight: 600 }} align="right">Total</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {lineItems.map((item, i) => {
                          const stock = getStock(item.product_id);
                          const noStock = item.product_id > 0 && !stock;
                          const overStock = stock && item.quantity > stock.available_quantity;
                          return (
                            <TableRow key={i}>
                              <TableCell>{item.product_name || products.find((p) => p.id === item.product_id)?.name}</TableCell>
                              <TableCell align="right">
                                <Typography variant="body2" color={(!stock || stock.available_quantity <= 0) ? 'error.main' : 'text.primary'}>
                                  {stock ? stock.available_quantity.toLocaleString() : '0'}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Typography color={(overStock || noStock) ? 'error.main' : 'text.primary'} fontWeight={(overStock || noStock) ? 700 : 400}>
                                  {item.quantity}
                                  {(overStock || noStock) && ' ⚠'}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">{formatCurrency(item.unit_price)}</TableCell>
                              <TableCell align="right">{formatCurrency(item.quantity * item.unit_price)}</TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5 }}>
                    <Typography variant="body2">Subtotal: {formatCurrency(subtotal)}</Typography>
                    <Typography variant="h6">Total: {formatCurrency(subtotal)}</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button disabled={activeStep === 0} onClick={handleBack}>Back</Button>
            <Box>
              {activeStep < steps.length - 1 ? (
                <Button variant="contained" onClick={handleNext} disabled={!valid()}>Next</Button>
              ) : (
                <Button variant="contained" onClick={handleSubmit} disabled={!valid() || submitting}>
                  {submitting ? 'Submitting...' : 'Create Order'}
                </Button>
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
