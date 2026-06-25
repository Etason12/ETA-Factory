import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, IconButton, TextField, Tooltip } from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { rawMaterialsApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { RawMaterial } from '../../types';
import { formatCurrency } from '../../utils/format';

export default function RawMaterialsPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager');
  const canDelete = hasRole('Owner', 'General Manager');
  const [data, setData] = useState<RawMaterial[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (search.trim()) params.search = search.trim();
      const res = await rawMaterialsApi.list(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this raw material?')) return;
    try {
      await rawMaterialsApi.delete(id);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to delete raw material');
    }
  };

  const columns = [
    { id: 'sku', label: 'SKU' },
    { id: 'name', label: 'Name' },
    { id: 'unit_name', label: 'Unit' },
    {
      id: 'cost_price',
      label: 'Unit Cost',
      render: (row: RawMaterial) => formatCurrency(Number(row.cost_price)),
    },
    {
      id: 'stock_quantity',
      label: 'Stock',
      render: (row: RawMaterial) => Number(row.stock_quantity || 0).toFixed(2),
    },
    {
      id: 'is_active',
      label: 'Status',
      render: (row: RawMaterial) => <StatusChip status={row.is_active ? 'Active' : 'Inactive'} />,
    },
    {
      id: 'actions',
      label: 'Actions',
      width: 100,
      render: (row: RawMaterial) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View">
            <IconButton size="small" onClick={() => navigate(`/raw-materials/${row.id}/view`)}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => navigate(`/raw-materials/${row.id}/edit`)}>
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
        title="Raw Materials"
        subtitle="Manage raw materials used in production"
        action={{ label: 'New Raw Material', path: '/raw-materials/new' }}
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
