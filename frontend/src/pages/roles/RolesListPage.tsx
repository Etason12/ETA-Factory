import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, IconButton, Tooltip, Typography, Chip, Dialog, DialogTitle,
  DialogContent, DialogContentText, DialogActions, Button, Snackbar, Alert,
} from '@mui/material';
import { Edit, Delete, Add, Security } from '@mui/icons-material';
import { rolesApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { Role } from '../../types';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';

export default function RolesListPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuthStore();
  const canEdit = hasRole('Owner', 'General Manager');
  const canDelete = hasRole('Owner');

  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState<Role | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const fetchRoles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await rolesApi.list();
      setRoles(data);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load roles');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchRoles(); }, [fetchRoles]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await rolesApi.delete(deleteTarget.id);
      setSuccess(`Role "${deleteTarget.name}" deleted`);
      setDeleteTarget(null);
      fetchRoles();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to delete role');
    } finally {
      setDeleting(false);
    }
  };

  const columns = [
    { id: 'name', label: 'Role Name' },
    { id: 'description', label: 'Description', render: (row: Role) => row.description || '-' },
    {
      id: 'is_system', label: 'Type',
      render: (row: Role) => row.is_system
        ? <Chip label="System" size="small" color="primary" variant="outlined" />
        : <Chip label="Custom" size="small" variant="outlined" />,
    },
    {
      id: 'actions', label: 'Actions', sortable: false, nowrap: true,
      render: (row: Role) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {canEdit && (
            <Tooltip title="Edit Role">
              <IconButton size="small" onClick={() => navigate(`/roles/${row.id}/edit`)}>
                <Edit fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Manage Permissions">
            <IconButton size="small" color="primary" onClick={() => navigate(`/roles/permissions?role_id=${row.id}`)}>
              <Security fontSize="small" />
            </IconButton>
          </Tooltip>
          {canDelete && !row.is_system && (
            <Tooltip title="Delete Role">
              <IconButton size="small" color="error" onClick={() => setDeleteTarget(row)}>
                <Delete fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Roles"
        subtitle="Manage system roles and permissions"
        action={canEdit ? { label: 'New Role', path: '/roles/new', icon: <Add /> } : undefined}
      />
      <DataTable
        columns={columns}
        data={roles}
        loading={loading}
        total={roles.length}
        page={1}
        perPage={roles.length}
      />
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete Role</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete <strong>{deleteTarget?.name}</strong>?
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={!!success} autoHideDuration={3000} onClose={() => setSuccess('')}>
        <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>
      </Snackbar>
      <Snackbar open={!!error} autoHideDuration={5000} onClose={() => setError('')}>
        <Alert severity="error" onClose={() => setError('')}>{error}</Alert>
      </Snackbar>
    </Box>
  );
}
