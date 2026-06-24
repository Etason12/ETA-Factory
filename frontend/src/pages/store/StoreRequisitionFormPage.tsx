import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, TextField, Button, Paper, Grid2 as Grid, MenuItem,
  Table, TableHead, TableBody, TableRow, TableCell, IconButton, Autocomplete,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import { storeApi, warehousesApi, rawMaterialsApi } from '../../api/endpoints';
import { todayStr } from '../../utils/format';

export default function StoreRequisitionFormPage() {
  const { id } = useParams();
  const isView = window.location.pathname === `/store/requisitions/${id}` && Boolean(id);
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [rawMaterials, setRawMaterials] = useState<any[]>([]);
  const [req, setReq] = useState<any>(null);
  const [form, setForm] = useState({
    warehouse_id: 0,
    production_batch_id: '',
    requisition_date: todayStr,
    notes: '',
  });
  const [items, setItems] = useState<any[]>([{ raw_material_id: 0, quantity_requested: 0 }]);

  useEffect(() => {
    Promise.all([
      warehousesApi.list({ per_page: 1000 }),
      rawMaterialsApi.list({ per_page: 1000 }),
    ]).then(([wRes, rmRes]) => {
      setWarehouses(wRes.items || []);
      setRawMaterials(rmRes.raw_materials || []);
    });
  }, []);

  useEffect(() => {
    if (!id) return;
    storeApi.requisitions.get(Number(id)).then((r: any) => {
      setReq(r);
      setForm({
        warehouse_id: r.warehouse_id,
        production_batch_id: r.production_batch_id || '',
        requisition_date: r.requisition_date?.split('T')[0] || '',
        notes: r.notes || '',
      });
      if (r.items) setItems(r.items);
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
    setItems([...items, { raw_material_id: 0, quantity_requested: 0 }]);
  };

  const removeItem = (index: number) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.warehouse_id) { alert('Please select a warehouse'); return; }
    const validItems = items.filter(i => i.raw_material_id && Number(i.quantity_requested) > 0);
    if (validItems.length === 0) { alert('At least one valid item is required'); return; }
    setSubmitting(true);
    try {
      await storeApi.requisitions.create({ ...form, production_batch_id: form.production_batch_id ? Number(form.production_batch_id) : null, items: validItems });
      navigate('/store/requisitions');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to create');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!id) return;
    try {
      await storeApi.requisitions.approve(Number(id));
      navigate('/store/requisitions');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to approve');
    }
  };

  const handleIssue = async () => {
    if (!id) return;
    try {
      await storeApi.requisitions.issue(Number(id));
      navigate('/store/requisitions');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to issue');
    }
  };

  const handleCancel = async () => {
    if (!id || !window.confirm('Cancel this requisition?')) return;
    try {
      await storeApi.requisitions.cancel(Number(id));
      navigate('/store/requisitions');
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to cancel');
    }
  };

  const canEdit = !req || req.status === 'Pending';

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/store/requisitions')}>Back</Button>
        <Typography variant="h4">
          {isView ? `Requisition ${req?.requisition_number || ''}` : 'New Store Requisition'}
        </Typography>
      </Box>
      <Paper sx={{ p: 3, maxWidth: 960 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2.5}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Warehouse *" select required disabled={isView || !canEdit}
                value={form.warehouse_id}
                onChange={(e: any) => setForm({ ...form, warehouse_id: Number(e.target.value) })}
              >
                <MenuItem value={0} disabled>Select warehouse</MenuItem>
                {warehouses.map((w: any) => (
                  <MenuItem key={w.id} value={w.id}>{w.name} - {w.code}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Requisition Date" type="date" disabled={isView || !canEdit}
                value={form.requisition_date} onChange={handleChange('requisition_date')}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Production Batch ID (optional)" type="number" disabled={isView || !canEdit}
                value={form.production_batch_id} onChange={handleChange('production_batch_id')}
                helperText="Link to a production batch if applicable"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth label="Notes" disabled={isView || !canEdit}
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
                      <TableCell align="right">Qty Requested</TableCell>
                      {req && <TableCell align="right">Qty Issued</TableCell>}
                      {(canEdit && !isView) && <TableCell align="center">Action</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell sx={{ minWidth: 250 }}>
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
                          {isView || !canEdit ? item.quantity_requested : (
                            <TextField type="number" size="small" sx={{ maxWidth: 120 }}
                              value={item.quantity_requested}
                              onChange={(e) => handleItemChange(idx, 'quantity_requested', Number(e.target.value))}
                              inputProps={{ min: 0 }}
                            />
                          )}
                        </TableCell>
                        {req && <TableCell align="right">{item.quantity_issued || 0}</TableCell>}
                        {(canEdit && !isView) && (
                          <TableCell align="center">
                            <IconButton size="small" color="error" onClick={() => removeItem(idx)} disabled={items.length <= 1}>
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
              {canEdit && !isView && (
                <Button startIcon={<AddIcon />} onClick={addItem} sx={{ mt: 1 }}>Add Item</Button>
              )}
            </Grid>

            <Grid size={12}>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                <Button variant="outlined" onClick={() => navigate('/store/requisitions')}>
                  {isView ? 'Back' : 'Cancel'}
                </Button>
                {req && req.status === 'Pending' && (
                  <>
                    <Button variant="contained" color="success" startIcon={<CheckCircleIcon />} onClick={handleApprove}>
                      Approve
                    </Button>
                    <Button variant="outlined" color="error" onClick={handleCancel}>Cancel</Button>
                  </>
                )}
                {req && req.status === 'Approved' && (
                  <Button variant="contained" startIcon={<LocalShippingIcon />} onClick={handleIssue}>
                    Issue Materials
                  </Button>
                )}
                {!isView && canEdit && (
                  <Button type="submit" variant="contained" startIcon={<SaveIcon />} disabled={submitting}>
                    {submitting ? 'Saving...' : 'Save'}
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </>
  );
}
