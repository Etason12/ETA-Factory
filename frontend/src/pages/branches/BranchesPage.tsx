import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, IconButton, Tooltip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { branchesApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { Branch } from '../../types';

export default function BranchesPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager');
  const canCreate = hasRole('Owner', 'General Manager');
  const [data, setData] = useState<Branch[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);

  const fetchBranches = useCallback(async () => {
    setLoading(true);
    try {
      const res = await branchesApi.list({ page, per_page: perPage });
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage]);

  useEffect(() => {
    fetchBranches();
  }, [fetchBranches]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this branch?')) return;
    try {
      await branchesApi.delete(id);
      fetchBranches();
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to delete branch');
    }
  };

  const columns = [
    { id: 'name', label: 'Name' },
    { id: 'code', label: 'Code' },
    { id: 'city', label: 'City' },
    { id: 'address', label: 'Address' },
    { id: 'phone', label: 'Phone' },
    { id: 'email', label: 'Email' },
    {
      id: 'is_active',
      label: 'Status',
      render: (row: Branch) => <StatusChip status={row.is_active ? 'Active' : 'Inactive'} />,
    },
    {
      id: 'actions',
      label: 'Actions',
      width: 140,
      render: (row: Branch) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View Warehouses">
            <IconButton size="small" onClick={() => navigate(`/warehouses?branch_id=${row.id}`)}>
              <WarehouseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => navigate(`/branches/${row.id}/edit`)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {canEdit && (
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
        title="Branches"
        subtitle="Manage company branches"
        action={canCreate ? { label: 'New Branch', path: '/branches/new' } : undefined}
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
