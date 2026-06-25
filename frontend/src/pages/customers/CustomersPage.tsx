import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, IconButton, TextField, Tooltip } from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { customersApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { Customer } from '../../types';

export default function CustomersPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager', 'Branch Manager', 'Sales Manager');
  const canDelete = hasRole('Owner', 'General Manager');
  const canCreate = hasRole('Owner', 'General Manager', 'Sales Officer', 'Sales Manager', 'Branch Manager');
  const [data, setData] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (search.trim()) params.search = search.trim();
      const res = await customersApi.list(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search]);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this customer?')) return;
    try {
      await customersApi.delete(id);
      fetchCustomers();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to delete customer');
    }
  };

  const columns = [
    { id: 'customer_code', label: 'Customer Code' },
    { id: 'name', label: 'Name' },
    { id: 'phone', label: 'Phone' },
    { id: 'email', label: 'Email' },
    { id: 'tin_number', label: 'TIN Number' },
    { id: 'customer_type', label: 'Type' },
    { id: 'branch_id', label: 'Branch ID' },
    {
      id: 'is_active',
      label: 'Status',
      render: (row: Customer) => <StatusChip status={row.is_active ? 'Active' : 'Inactive'} />,
    },
    {
      id: 'actions',
      label: 'Actions',
      width: 130,
      render: (row: Customer) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View">
            <IconButton size="small" onClick={() => navigate(`/customers/${row.id}/edit`)}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => navigate(`/customers/${row.id}/edit`)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {canDelete && (
            <Tooltip title="Delete">
              <IconButton size="small" color="error" onClick={() => handleDelete(row.id)}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Customers"
        subtitle="Manage your customer records"
        action={canCreate ? { label: 'New Customer', path: '/customers/new' } : undefined}
      />
      <TextField
        size="small"
        placeholder="Search by name or customer code..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        sx={{ mb: 2, width: 320 }}
      />
      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />
    </>
  );
}
