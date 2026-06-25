import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Card, CardContent, Typography, Avatar, IconButton, TextField, Tooltip, Grid2 as Grid, Skeleton,
} from '@mui/material';
import InventoryIcon from '@mui/icons-material/Inventory';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CategoryIcon from '@mui/icons-material/Category';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { productsApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { Product } from '../../types';
import { formatCurrency } from '../../utils/format';

function SummaryCard({ icon, label, value, color, loading }: {
  icon: React.ReactNode; label: string; value: string | number; color: string; loading?: boolean;
}) {
  return (
    <Card>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, '&:last-child': { pb: 2 } }}>
        <Avatar sx={{ bgcolor: `${color}.main`, width: 44, height: 44 }}>{icon}</Avatar>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {loading ? (
            <><Skeleton width={60} height={28} /><Skeleton width={90} height={18} /></>
          ) : (
            <>
              <Typography variant="h5" fontWeight={600}>{value}</Typography>
              <Typography variant="body2" color="text.secondary" noWrap>{label}</Typography>
            </>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

export default function ProductsPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager');
  const canDelete = hasRole('Owner', 'General Manager');
  const canCreate = canEdit;
  const [data, setData] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [summary, setSummary] = useState({ active: 0, categories: 0, total_value: 0 });

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (search.trim()) params.search = search.trim();
      const [res, allRes] = await Promise.all([
        productsApi.list(params),
        page === 1 && !search ? null : productsApi.list({ per_page: 10000 }).catch(() => null),
      ]);
      setData(res.items || []);
      setTotal(res.total || 0);
      const fullData = page === 1 && !search ? res : allRes;
      if (fullData) {
        const items = fullData.items || [];
        setSummary({
          active: items.filter((p: Product) => p.is_active).length,
          categories: new Set(items.map((p: Product) => p.category_name).filter(Boolean)).size,
          total_value: items.reduce((s: number, p: Product) => s + Number(p.unit_price || 0), 0),
        });
      } else if (page === 1 && !search) {
        const items = res.items || [];
        setSummary({
          active: items.filter((p: Product) => p.is_active).length,
          categories: new Set(items.map((p: Product) => p.category_name).filter(Boolean)).size,
          total_value: items.reduce((s: number, p: Product) => s + Number(p.unit_price || 0), 0),
        });
      }
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
      id: 'costing_method', label: 'Costing',
      render: (row: Product) => {
        const labels: Record<string, string> = {
          standard: 'Standard', weighted_average: 'Avg Cost', fifo: 'FIFO',
        };
        return labels[row.costing_method || 'standard'] || '-';
      },
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
          <Tooltip title="BOM">
            <IconButton size="small" onClick={() => navigate(`/products/${row.id}/bom`)}>
              <AccountTreeIcon fontSize="small" />
            </IconButton>
          </Tooltip>
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
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <SummaryCard icon={<InventoryIcon />} label="Total Products" value={total} color="primary" loading={loading} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <SummaryCard icon={<CheckCircleIcon />} label="Active Products" value={summary.active} color="success" loading={loading} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <SummaryCard icon={<CategoryIcon />} label="Categories" value={summary.categories} color="info" loading={loading} />
        </Grid>
      </Grid>
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
