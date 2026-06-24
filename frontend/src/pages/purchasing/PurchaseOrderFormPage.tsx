import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, TextField, Button, Paper, Grid2 as Grid, MenuItem,
  Table, TableHead, TableBody, TableRow, TableCell, IconButton,
  Dialog, DialogTitle, DialogContent, DialogActions,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { purchasingApi, suppliersApi, rawMaterialsApi, warehousesApi } from '../../api/endpoints';
import { formatCurrency, todayStr } from '../../utils/format';

export default function PurchaseOrderFormPage() {
  const { id } = useParams();
  const isView = window.location.pathname === `/purchasing/orders/${id}` && Boolean(id);
  const isEdit = Boolean(id) && !isView;
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [rawMaterials, setRawMaterials] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [receiveDialogOpen, setReceiveDialogOpen] = useState(false);
  const [receiveWarehouseId, setReceiveWarehouseId] = useState<number>(0);
  const [receiveItems, setReceiveItems] = useState<any[]>([]);
  const [form, setForm] = useState({
    order_number: `PO-${Date.now()}`,
    supplier_id: 0,
    order_date: todayStr,
    expected_date: todayStr,
    notes: '',
  });
  const [items, setItems] = useState<any[]>([{ raw_material_id: 0, quantity_ordered: 0, unit_cost: 0 }]);
  const [po, setPo] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      suppliersApi.list({ per_page: 1000 }),
      rawMaterialsApi.list({ per_page: 1000 }),
      warehousesApi.list({ per_page: 1000 }),
    ]).then(([sRes, rmRes, wRes]) => {
      setSuppliers(sRes.suppliers || []);
      setRawMaterials(rmRes.raw_materials || []);
      setWarehouses(wRes.items || []);
      if ((wRes.items || []).length > 0) setReceiveWarehouseId(wRes.items[0].id);
    });
  }, []);

  useEffect(() => {
    if (!id) return;
    purchasingApi.get(Number(id)).then((po: any) => {
      setPo(po);
      setForm({
        order_number: po.order_number,
        supplier_id: po.supplier_id,
        order_date: po.order_date?.split('T')[0] || '',
        expected_date: po.expected_date?.split('T')[0] || todayStr,
        notes: po.notes || '',
      });
      if (po.items) setItems(po.items);
    });
  }, [id]);

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [field]: e.target.value });
  };

  const handleItemChange = (index: number, field: string, value: any) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    setItems(updated);
  };

  const addItem = () => {
    setItems([...items, { raw_material_id: 0, quantity_ordered: 0, unit_cost: 0 }]);
  };

  const removeItem = (index: number) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.supplier_id) { alert('Please select a supplier'); return; }
    const validItems = items.filter(i => i.raw_material_id && Number(i.quantity_ordered) > 0 && Number(i.unit_cost) >= 0);
    if (validItems.length === 0) { alert('At least one valid item is required'); return; }
    setSubmitting(true);
    try {
      if (isEdit) {
        await purchasingApi.update(Number(id), { ...form, items: validItems });
      } else {
        await purchasingApi.create({ ...form, items: validItems });
      }
      navigate('/purchasing/orders');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to save');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitForApproval = async () => {
    if (!id) return;
    try {
      await purchasingApi.submit(Number(id));
      navigate('/purchasing/orders');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to submit');
    }
  };

  const openReceiveDialog = () => {
    setReceiveItems(items.map(i => ({
      item_id: i.id,
      raw_material_name: i.raw_material_name || `RM #${i.raw_material_id}`,
      quantity_ordered: Number(i.quantity_ordered),
      quantity_received: Number(i.quantity_received || 0),
      to_receive: Number(i.quantity_ordered) - Number(i.quantity_received || 0),
    })));
    setReceiveDialogOpen(true);
  };

  const handleReceiveConfirm = async () => {
    if (!id || !receiveWarehouseId) { alert('Please select a warehouse'); return; }
    const valid = receiveItems.filter(i => i.to_receive > 0);
    if (valid.length === 0) { alert('No items to receive'); return; }
    try {
      await purchasingApi.receive(Number(id), {
        warehouse_id: receiveWarehouseId,
        items: valid.map(i => ({ item_id: i.item_id, quantity_received: i.to_receive })),
      });
      setReceiveDialogOpen(false);
      navigate('/purchasing/orders');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to receive goods');
    }
  };

  const handleCancel = async () => {
    if (!id || !window.confirm('Cancel this purchase order?')) return;
    try {
      await purchasingApi.cancel(Number(id));
      navigate('/purchasing/orders');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to cancel');
    }
  };

  const total = items.reduce((sum, i) => sum + (Number(i.quantity_ordered) || 0) * (Number(i.unit_cost) || 0), 0);
  const canEdit = !po || po.status === 'Draft';

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/purchasing/orders')}>Back</Button>
        <Typography variant="h4">
          {isEdit ? 'Edit Purchase Order' : isView ? `PO ${form.order_number}` : 'New Purchase Order'}
        </Typography>
      </Box>
      <Paper sx={{ p: 3, maxWidth: 960 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2.5}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Order Number" disabled={isView}
                value={form.order_number} onChange={handleChange('order_number')}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Supplier *" select required disabled={isView || !canEdit}
                value={form.supplier_id}
                onChange={(e: any) => setForm({ ...form, supplier_id: Number(e.target.value) })}
              >
                <MenuItem value={0} disabled>Select supplier</MenuItem>
                {suppliers.map((s: any) => (
                  <MenuItem key={s.id} value={s.id}>{s.name} ({s.code})</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Order Date" type="date" disabled={isView || !canEdit}
                value={form.order_date} onChange={handleChange('order_date')}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Expected Date" type="date" disabled={isView || !canEdit}
                value={form.expected_date} onChange={handleChange('expected_date')}
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth label="Notes" multiline rows={2} disabled={isView || !canEdit}
                value={form.notes} onChange={handleChange('notes')}
              />
            </Grid>

            <Grid size={12}>
              <Typography variant="h6" gutterBottom>Items</Typography>
              <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Raw Material</TableCell>
                      <TableCell align="right">Qty Ordered</TableCell>
                      <TableCell align="right">Unit Cost</TableCell>
                      <TableCell align="right">Line Total</TableCell>
                      {(canEdit && !isView) && <TableCell align="center">Action</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell>
                          {isView || !canEdit ? (
                            item.raw_material_name || `RM #${item.raw_material_id}`
                          ) : (
                            <TextField select size="small" fullWidth
                              value={item.raw_material_id}
                              onChange={(e: any) => handleItemChange(idx, 'raw_material_id', Number(e.target.value))}
                            >
                              <MenuItem value={0} disabled>Select</MenuItem>
                              {rawMaterials.map((rm: any) => (
                                <MenuItem key={rm.id} value={rm.id}>{rm.name} ({rm.sku})</MenuItem>
                              ))}
                            </TextField>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          {isView || !canEdit ? item.quantity_ordered : (
                            <TextField type="number" size="small" sx={{ maxWidth: 100 }}
                              value={item.quantity_ordered}
                              onChange={(e) => handleItemChange(idx, 'quantity_ordered', Number(e.target.value))}
                              inputProps={{ min: 0 }}
                            />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          {isView || !canEdit ? formatCurrency(item.unit_cost) : (
                            <TextField type="number" size="small" sx={{ maxWidth: 120 }}
                              value={item.unit_cost}
                              onChange={(e) => handleItemChange(idx, 'unit_cost', Number(e.target.value))}
                              inputProps={{ min: 0, step: 0.01 }}
                            />
                          )}
                        </TableCell>
                        <TableCell align="right">{formatCurrency((item.quantity_ordered || 0) * (item.unit_cost || 0))}</TableCell>
                        {(canEdit && !isView) && (
                          <TableCell align="center">
                            <IconButton size="small" color="error" onClick={() => removeItem(idx)} disabled={items.length <= 1}>
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                    <TableRow>
                      <TableCell colSpan={3} align="right"><Typography fontWeight={700}>Total</Typography></TableCell>
                      <TableCell align="right"><Typography fontWeight={700}>{formatCurrency(total)}</Typography></TableCell>
                      {(canEdit && !isView) && <TableCell />}
                    </TableRow>
                  </TableBody>
                </Table>
              </Paper>
              {canEdit && !isView && (
                <Button startIcon={<AddIcon />} onClick={addItem} sx={{ mt: 1 }}>Add Item</Button>
              )}
            </Grid>

            <Grid size={12}>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                <Button variant="outlined" onClick={() => navigate('/purchasing/orders')}>
                  {isView ? 'Back' : 'Cancel'}
                </Button>
                {po && po.status === 'Draft' && (
                  <>
                    <Button variant="contained" color="success" onClick={handleSubmitForApproval}>
                      Submit (Order)
                    </Button>
                    <Button variant="outlined" color="error" onClick={handleCancel}>Cancel Order</Button>
                  </>
                )}
                {po && (po.status === 'Ordered' || po.status === 'PartiallyReceived') && (
                  <Button variant="contained" onClick={openReceiveDialog}>
                    {po.status === 'PartiallyReceived' ? 'Receive More' : 'Receive Goods'}
                  </Button>
                )}
                {!isView && (
                  <Button type="submit" variant="contained" startIcon={<SaveIcon />} disabled={submitting || !canEdit}>
                    {submitting ? 'Saving...' : 'Save'}
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>
      {/* Receive Goods Dialog */}
      <Dialog open={receiveDialogOpen} onClose={() => setReceiveDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Receive Goods</DialogTitle>
        <DialogContent>
          <TextField select size="small" fullWidth label="Warehouse *" value={receiveWarehouseId}
            onChange={(e: any) => setReceiveWarehouseId(Number(e.target.value))} sx={{ mb: 2, mt: 1 }}
          >
            <MenuItem value={0} disabled>Select warehouse</MenuItem>
            {warehouses.map((w: any) => (
              <MenuItem key={w.id} value={w.id}>{w.name} - {w.code}</MenuItem>
            ))}
          </TextField>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Raw Material</TableCell>
                <TableCell align="right">Ordered</TableCell>
                <TableCell align="right">Previously Received</TableCell>
                <TableCell align="right">To Receive</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {receiveItems.map((ri, idx) => (
                <TableRow key={ri.item_id || idx}>
                  <TableCell>{ri.raw_material_name}</TableCell>
                  <TableCell align="right">{ri.quantity_ordered}</TableCell>
                  <TableCell align="right">{ri.quantity_received}</TableCell>
                  <TableCell align="right">
                    <TextField type="number" size="small" sx={{ maxWidth: 120 }}
                      value={ri.to_receive}
                      onChange={(e) => {
                        const updated = [...receiveItems];
                        updated[idx] = { ...updated[idx], to_receive: Math.max(0, Math.min(Number(e.target.value), ri.quantity_ordered - ri.quantity_received)) };
                        setReceiveItems(updated);
                      }}
                      inputProps={{ min: 0, max: ri.quantity_ordered - ri.quantity_received, step: 0.01 }}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReceiveDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleReceiveConfirm}>Confirm Receipt</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
