import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, TextField, Table, TableHead, TableBody, TableRow, TableCell,
  IconButton, Chip, TablePagination, Typography, Paper,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PageHeader from '../../components/common/PageHeader';
import { suppliersApi } from '../../api/endpoints';

export default function SuppliersPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await suppliersApi.list({ page: page + 1, per_page: rowsPerPage, search });
      setItems(res.suppliers || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, [page, rowsPerPage]);

  useEffect(() => {
    if (page !== 0) setPage(0);
    else fetch();
  }, [search]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this supplier?')) return;
    try {
      await suppliersApi.delete(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to delete');
    }
  };

  return (
    <>
      <PageHeader title="Suppliers" subtitle="Manage raw material suppliers" />
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField size="small" label="Search" value={search} onChange={(e) => setSearch(e.target.value)} sx={{ minWidth: 250 }} />
        <Box sx={{ flex: 1 }} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/suppliers/new')}>
          New Supplier
        </Button>
      </Box>
      <Paper variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Code</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Contact Person</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((s: any) => (
              <TableRow key={s.id} hover>
                <TableCell>{s.code}</TableCell>
                <TableCell>{s.name}</TableCell>
                <TableCell>{s.contact_person || '-'}</TableCell>
                <TableCell>{s.phone || '-'}</TableCell>
                <TableCell>{s.email || '-'}</TableCell>
                <TableCell>
                  <Chip size="small" label={s.is_active ? 'Active' : 'Inactive'} color={s.is_active ? 'success' : 'default'} />
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => navigate(`/suppliers/${s.id}/view`)}><VisibilityIcon /></IconButton>
                  <IconButton size="small" onClick={() => navigate(`/suppliers/${s.id}/edit`)}><EditIcon /></IconButton>
                  <IconButton size="small" color="error" onClick={() => handleDelete(s.id)}><DeleteIcon /></IconButton>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow><TableCell colSpan={7} align="center" sx={{ py: 3, color: 'text.secondary' }}>No suppliers found</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination component="div" count={total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={rowsPerPage} onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }} />
      </Paper>
    </>
  );
}
