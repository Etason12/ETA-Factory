import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, IconButton, TextField, Tooltip } from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { productsApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { Product } from '../../types';
import { formatCurrency } from '../../utils/format';

export default function ProductsPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager');
  const canDelete = hasRole('Owner', 'General Manager');
  const canCreate = canEdit;
  const [data, setData] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (search.trim()) params.search = search.trim();
      const res = await productsApi.list(params);
      setData(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    try {
      await productsApi.delete(id);
      fetchProducts();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to delete product');
    }
  };

  const columns = [
    { id: 'sku', label: 'SKU' },
    { id: 'name', label: 'Name' },
    { id: 'category_name', label: 'Category' },
    { id: 'unit_name', label: 'Unit' },
    {
      id: 'unit_price',
      label: 'Unit Price',
      render: (row: Product) => formatCurrency(Number(row.unit_price)),
    },
    {
      id: 'min_stock_level',
      label: 'Min',
      render: (row: Product) => (row.min_stock_level && row.min_stock_level > 0 ? row.min_stock_level : '-'),
    },
    {
      id: 'max_stock_level',
      label: 'Max',
      render: (row: Product) => (row.max_stock_level && row.max_stock_level > 0 ? row.max_stock_level : '-'),
    },
    {
      id: 'is_active',
      label: 'Status',
      render: (row: Product) => <StatusChip status={row.is_active ? 'Active' : 'Inactive'} />,
    },
    {
      id: 'actions',
      label: 'Actions',
      width: 130,
      render: (row: Product) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View">
            <IconButton size="small" onClick={() => navigate(`/products/${row.id}/view`)}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => navigate(`/products/${row.id}/edit`)}>
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
        title="Products"
        subtitle="Manage your product catalog"
        action={canCreate ? { label: 'New Product', path: '/products/new' } : undefined}
      />
      <TextField
        size="small"
        placeholder="Search by name or SKU..."
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
