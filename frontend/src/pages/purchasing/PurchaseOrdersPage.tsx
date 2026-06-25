import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, TextField, Table, TableHead, TableBody, TableRow, TableCell,
  IconButton, Chip, TablePagination, MenuItem, Paper,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import PageHeader from '../../components/common/PageHeader';
import { purchasingApi, suppliersApi } from '../../api/endpoints';

const STATUSES = ['Draft', 'Ordered', 'PartiallyReceived', 'FullyReceived', 'Cancelled'];

export default function PurchaseOrdersPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [supplierId, setSupplierId] = useState<number>(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    suppliersApi.list({ per_page: 1000 }).then(r => setSuppliers(r.suppliers || []));
  }, []);

  const fetch = async () => {
    setLoading(true);
    try {
      const params: any = { page: page + 1, per_page: rowsPerPage, status };
      if (supplierId) params.supplier_id = supplierId;
      const res = await purchasingApi.list(params);
      setItems(res.orders || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this purchase order?')) return;
    try {
      await purchasingApi.delete(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to delete');
    }
  };

  useEffect(() => { fetch(); }, [page, rowsPerPage, status, supplierId]);

  return (
    <>
      <PageHeader title="Purchase Orders" subtitle="Procure raw materials from suppliers" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField select size="small" label="Status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(0); }} sx={{ minWidth: 150 }}>
          <MenuItem value="">All</MenuItem>
          {STATUSES.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Supplier" value={supplierId} onChange={(e: any) => { setSupplierId(Number(e.target.value)); setPage(0); }} sx={{ minWidth: 200 }}>
          <MenuItem value={0}>All Suppliers</MenuItem>
          {suppliers.map((s: any) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
        </TextField>
        <Box sx={{ flex: 1 }} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/purchasing/orders/new')}>
          New Purchase Order
        </Button>
      </Box>
      <Paper variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Order #</TableCell>
              <TableCell>Supplier</TableCell>
              <TableCell>Order Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created By</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((po: any) => (
              <TableRow key={po.id} hover>
                <TableCell>{po.order_number}</TableCell>
                <TableCell>{po.supplier_name}</TableCell>
                <TableCell>{po.order_date}</TableCell>
                <TableCell>
                  <Chip size="small" label={po.status}
                    color={po.status === 'Draft' ? 'default' : po.status === 'Ordered' ? 'info' : po.status === 'FullyReceived' ? 'success' : po.status === 'Cancelled' ? 'error' : 'warning'} />
                </TableCell>
                <TableCell>{po.created_by_name || '-'}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => navigate(`/purchasing/orders/${po.id}`)}><VisibilityIcon /></IconButton>
                  {po.status === 'Draft' && (
                    <IconButton size="small" onClick={() => navigate(`/purchasing/orders/${po.id}/edit`)}><EditIcon /></IconButton>
                  )}
                  {po.status === 'Draft' && (
                    <IconButton size="small" onClick={() => handleDelete(po.id)}><DeleteIcon /></IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow><TableCell colSpan={6} align="center" sx={{ py: 3, color: 'text.secondary' }}>No purchase orders found</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination component="div" count={total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={rowsPerPage} onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }} />
      </Paper>
    </>
  );
}
