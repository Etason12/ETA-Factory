import { useState, useEffect } from 'react';
import { Box, Button, TextField, MenuItem, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, CircularProgress } from '@mui/material';
import { warehousesApi } from '../../api/endpoints';
import type { Warehouse, Inventory } from '../../types';
import PageHeader from '../../components/common/PageHeader';

export default function StocktakePage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState<number | string>('');
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [loading, setLoading] = useState(false);
  const [counts, setCounts] = useState<Record<number, number>>({});

  useEffect(() => {
    warehousesApi.list({ per_page: 1000 }).then(res => setWarehouses(res.items || []));
  }, []);

  const loadInventory = async (warehouseId: number) => {
    setLoading(true);
    const inv = await warehousesApi.inventory(warehouseId);
    setInventory(inv);
    setCounts(inv.reduce((acc: Record<number, number>, item: any) => ({ ...acc, [item.product_id]: item.quantity_on_hand }), {}));
    setLoading(false);
  };

  const handleSubmit = async () => {
    if (!selectedWarehouse) { alert('Please select a warehouse'); return; }
    const discrepancies = inventory
      .filter(item => counts[item.product_id] !== undefined && counts[item.product_id] !== item.quantity_on_hand)
      .map(item => ({
        product_id: item.product_id,
        current_quantity: item.quantity_on_hand,
        adjusted_quantity: counts[item.product_id],
      }));
    if (discrepancies.length === 0) { alert('No discrepancies found. Stocktake complete.'); return; }
    try {
      await warehousesApi.createAdjustment({
        adjustment_number: `STK-${Date.now()}`,
        warehouse_id: selectedWarehouse,
        adjustment_type: 'Stocktake',
        notes: 'Physical stocktake adjustment',
        items: discrepancies,
      });
      alert(`Stocktake submitted. ${discrepancies.length} item(s) adjusted.`);
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to submit stocktake');
    }
  };

  return (
    <Box>
      <PageHeader title="Stocktake" subtitle="Physical inventory reconciliation" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <TextField select label="Warehouse" value={selectedWarehouse} sx={{ width: 250 }} 
          onChange={(e) => { 
            const wId = Number(e.target.value);
            setSelectedWarehouse(wId);
            loadInventory(wId);
          }}>
          <MenuItem value="" disabled><em>Select a warehouse</em></MenuItem>
          {warehouses.map(w => <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>)}
        </TextField>
      </Box>
      {loading ? <CircularProgress /> : inventory.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Product</TableCell>
                <TableCell>System Qty</TableCell>
                <TableCell>Counted Qty</TableCell>
                <TableCell>Difference</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {inventory.map(item => {
                const counted = counts[item.product_id] ?? 0;
                const diff = counted - item.quantity_on_hand;
                return (
                  <TableRow key={item.product_id}>
                    <TableCell>{item.product_name}</TableCell>
                    <TableCell>{item.quantity_on_hand}</TableCell>
                    <TableCell>
                      <TextField type="number" size="small" value={counted} 
                        onChange={(e) => setCounts({...counts, [item.product_id]: Number(e.target.value)})} />
                    </TableCell>
                    <TableCell sx={{ color: diff === 0 ? 'inherit' : diff > 0 ? 'success.main' : 'error.main' }}>
                      {diff}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      <Button variant="contained" sx={{ mt: 2 }} onClick={handleSubmit} disabled={loading || inventory.length === 0}>
        Submit Stocktake
      </Button>
    </Box>
  );
}
