import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, IconButton, Tooltip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import StatusChip from '../../components/common/StatusChip';
import { usersApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { User } from '../../types';

export default function UsersPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager');
  const canDelete = hasRole('Owner');
  const canCreate = canEdit;
  const [data, setData] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [loading, setLoading] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await usersApi.list({ page, per_page: perPage });
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      await usersApi.delete(id);
      fetchUsers();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to delete user');
    }
  };

  const columns = [
    { id: 'username', label: 'Username' },
    { id: 'full_name', label: 'Full Name' },
    { id: 'email', label: 'Email' },
    { id: 'role_name', label: 'Role' },
    {
      id: 'is_active',
      label: 'Status',
      render: (row: User) => <StatusChip status={row.is_active ? 'Active' : 'Inactive'} />,
    },
    {
      id: 'last_login',
      label: 'Last Login',
      render: (row: User) => (row.last_login ? new Date(row.last_login).toLocaleString() : '-'),
    },
    {
      id: 'actions',
      label: 'Actions',
      width: 100,
      render: (row: User) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {canEdit && (
            <Tooltip title="Edit">
              <IconButton size="small" onClick={() => navigate(`/users/${row.id}/edit`)}>
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
        title="Users"
        subtitle="Manage system users"
        action={canCreate ? { label: 'New User', path: '/users/new' } : undefined}
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
