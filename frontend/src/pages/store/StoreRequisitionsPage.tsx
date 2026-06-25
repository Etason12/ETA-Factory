import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, TextField, Table, TableHead, TableBody, TableRow, TableCell,
  IconButton, Chip, TablePagination, MenuItem, Paper,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import { storeApi } from '../../api/endpoints';

const STATUSES = ['Pending', 'Approved', 'Issued', 'Cancelled'];

export default function StoreRequisitionsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await storeApi.requisitions.list({ page: page + 1, per_page: rowsPerPage, status });
      setItems(res.requisitions || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, [page, rowsPerPage, status]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this requisition?')) return;
    try {
      await storeApi.requisitions.delete(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.message || 'Failed to delete');
    }
  };

  return (
    <>
      <PageHeader title="Store Requisitions" subtitle="Request raw materials from store for production" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField select size="small" label="Status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(0); }} sx={{ minWidth: 180 }}>
          <MenuItem value="">All</MenuItem>
          {STATUSES.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
        </TextField>
        <Box sx={{ flex: 1 }} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/store/requisitions/new')}>
          New Requisition
        </Button>
      </Box>
      <Paper variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Requisition #</TableCell>
              <TableCell>Warehouse</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created By</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((r: any) => (
              <TableRow key={r.id} hover>
                <TableCell>{r.requisition_number}</TableCell>
                <TableCell>{r.warehouse_name}</TableCell>
                <TableCell>{r.requisition_date}</TableCell>
                <TableCell>
                  <Chip size="small" label={r.status}
                    color={r.status === 'Pending' ? 'warning' : r.status === 'Approved' ? 'info' : r.status === 'Issued' ? 'success' : 'default'} />
                </TableCell>
                <TableCell>{r.created_by_name || '-'}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => navigate(`/store/requisitions/${r.id}`)}><VisibilityIcon /></IconButton>
                  {r.status === 'Pending' && (
                    <IconButton size="small" color="error" onClick={() => handleDelete(r.id)}><DeleteIcon fontSize="small" /></IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow><TableCell colSpan={6} align="center" sx={{ py: 3, color: 'text.secondary' }}>No requisitions found</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination component="div" count={total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={rowsPerPage} onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }} />
      </Paper>
    </>
  );
}
