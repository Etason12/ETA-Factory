import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, InputLabel, MenuItem, Select, TextField, Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell, Divider, Snackbar, Alert } from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import { productsApi, rawMaterialsApi } from '../../api/endpoints';
import type { Product, RawMaterial } from '../../types';
import { formatCurrency } from '../../utils/format';

export default function BOMManagementPage() {
  const { productId } = useParams<{ productId: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [components, setComponents] = useState<any[]>([]);
  const [rawMaterials, setRawMaterials] = useState<RawMaterial[]>([]);
  const [loading, setLoading] = useState(false);
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [newRMId, setNewRMId] = useState('');
  const [newQuantity, setNewQuantity] = useState('');
  const [totalMaterialCost, setTotalMaterialCost] = useState(0);
  const [laborCost, setLaborCost] = useState(0);
  const [utilityCost, setUtilityCost] = useState(0);
  const [savingCosts, setSavingCosts] = useState(false);
  const [snackbar, setSnackbar] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);
  const loaded = useRef(false);

  const syncCostPrice = async () => {
    if (!productId) return;
    try {
      const bomRes = await productsApi.getBom(Number(productId));
      const mc = Number(bomRes.material_cost || 0);
      const lc = Number(bomRes.labor_cost ?? product?.bom_labor_cost ?? 0);
      const uc = Number(bomRes.utility_cost ?? product?.bom_utility_cost ?? 0);
      await productsApi.update(Number(productId), { cost_price: mc + lc + uc });
    } catch { /* ignore */ }
  };

  const fetchBom = useCallback(async () => {
    if (!productId) return;
    setLoading(true);
    try {
      const [p, bomRes, rms] = await Promise.all([
        productsApi.get(Number(productId)),
        productsApi.getBom(Number(productId)),
        rawMaterialsApi.list({ per_page: 1000 })
      ]);
      setProduct(p);
      setComponents(bomRes.components || []);
      setTotalMaterialCost(bomRes.material_cost || 0);
      setLaborCost(bomRes.labor_cost ?? p.bom_labor_cost ?? 0);
      setUtilityCost(bomRes.utility_cost ?? p.bom_utility_cost ?? 0);
      setRawMaterials(rms.raw_materials || []);
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    if (!loaded.current) { loaded.current = true; fetchBom(); }
  }, [fetchBom]);

  const handleAdd = async () => {
    if (!productId || !newRMId || !newQuantity) return;
    try {
      await productsApi.addUpdateBom(Number(productId), {
        raw_material_id: Number(newRMId),
        quantity: Number(newQuantity)
      });
      setOpenAddDialog(false);
      setNewRMId('');
      setNewQuantity('');
      await fetchBom();
      await syncCostPrice();
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to add component');
    }
  };

  const handleDelete = async (rmId: number) => {
    if (!productId || !window.confirm('Are you sure you want to remove this raw material?')) return;
    try {
      await productsApi.deleteBom(Number(productId), rmId);
      await fetchBom();
      await syncCostPrice();
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to remove component');
    }
  };

  const handleSaveCosts = async () => {
    if (!productId) return;
    setSavingCosts(true);
    try {
      const total = totalMaterialCost + Number(laborCost) + Number(utilityCost);
      await productsApi.update(Number(productId), {
        bom_labor_cost: Number(laborCost),
        bom_utility_cost: Number(utilityCost),
        cost_price: total,
      });
      setSnackbar({ message: 'Cost settings saved successfully', severity: 'success' });
      await fetchBom();
    } catch (err: any) {
      setSnackbar({ message: err?.response?.data?.error || 'Failed to save costs', severity: 'error' });
    } finally {
      setSavingCosts(false);
    }
  };

  const totalCost = totalMaterialCost + Number(laborCost) + Number(utilityCost);

  if (!product) return null;

  return (
    <>
      <PageHeader title={`BOM for ${product.name}`} subtitle={`SKU: ${product.sku}`} />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <Button variant="contained" onClick={() => setOpenAddDialog(true)}>Add Raw Material</Button>
      </Box>

      <Paper variant="outlined" sx={{ mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Raw Material</TableCell>
              <TableCell>SKU</TableCell>
              <TableCell align="right">Qty per Unit</TableCell>
              <TableCell align="right">Unit Cost</TableCell>
              <TableCell align="right">Line Cost</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {components.map((comp: any) => (
              <TableRow key={comp.raw_material_id}>
                <TableCell>{comp.raw_material_name}</TableCell>
                <TableCell>{comp.raw_material_sku || '-'}</TableCell>
                <TableCell align="right">{comp.quantity} {comp.unit_name || ''}</TableCell>
                <TableCell align="right">{formatCurrency(comp.unit_cost || 0)}</TableCell>
                <TableCell align="right">{formatCurrency(comp.line_cost || 0)}</TableCell>
                <TableCell align="right">
                  <Button size="small" color="error" onClick={() => handleDelete(comp.raw_material_id)}>Remove</Button>
                </TableCell>
              </TableRow>
            ))}
            {components.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                  No raw materials added yet. Click "Add Raw Material" to create the recipe.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>Manufacturing Cost per Unit</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography>Raw Materials (from BOM)</Typography>
            <Typography fontWeight={600}>{formatCurrency(totalMaterialCost)}</Typography>
          </Box>
          <TextField
            size="small"
            type="number"
            label="Labor (Human Power) per Unit"
            value={laborCost}
            onChange={(e) => setLaborCost(Number(e.target.value))}
            inputProps={{ min: 0, step: 0.01 }}
            sx={{ maxWidth: 300 }}
          />
          <TextField
            size="small"
            type="number"
            label="Utilities (Electricity & Overhead) per Unit"
            value={utilityCost}
            onChange={(e) => setUtilityCost(Number(e.target.value))}
            inputProps={{ min: 0, step: 0.01 }}
            sx={{ maxWidth: 300 }}
          />
          <Divider />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle1" fontWeight={700}>Total Cost per Unit</Typography>
            <Typography variant="subtitle1" fontWeight={700}>{formatCurrency(totalCost)}</Typography>
          </Box>
          <Box>
            <Button variant="contained" size="small" onClick={handleSaveCosts} disabled={savingCosts}>
              {savingCosts ? 'Saving...' : 'Save Cost Settings'}
            </Button>
          </Box>
        </Box>
      </Paper>

      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Raw Material to BOM</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1, mb: 2 }}>
            <InputLabel>Raw Material</InputLabel>
            <Select value={newRMId} onChange={(e) => setNewRMId(e.target.value as string)}>
              {rawMaterials.map(rm => (
                <MenuItem key={rm.id} value={rm.id}>{rm.name} ({rm.sku}) - {formatCurrency(Number(rm.cost_price))}/ea</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Quantity per Unit"
            type="number"
            value={newQuantity}
            onChange={(e) => setNewQuantity(e.target.value)}
            helperText="How many units of this raw material to produce ONE finished product"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>Cancel</Button>
          <Button onClick={handleAdd} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!snackbar}
        autoHideDuration={4000}
        onClose={() => setSnackbar(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar(null)} severity={snackbar?.severity || 'success'} variant="filled">
          {snackbar?.message}
        </Alert>
      </Snackbar>
    </>
  );
}
