import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Box, Typography, Paper, Checkbox, FormControlLabel, Button,
  FormGroup, Divider, CircularProgress, Alert, Snackbar, Select,
  MenuItem, FormControl, InputLabel, Chip,
} from '@mui/material';
import { rolesApi } from '../../api/endpoints';
import type { Role, Permission } from '../../types';
import PageHeader from '../../components/common/PageHeader';

export default function RolePermissionsPage() {
  const [searchParams] = useSearchParams();
  const preselectedId = searchParams.get('role_id');
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(
    preselectedId ? Number(preselectedId) : null
  );
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [rolesData, permsData] = await Promise.all([
          rolesApi.list(),
          rolesApi.listPermissions(),
        ]);
        setRoles(rolesData);
        setPermissions(permsData);
        if (rolesData.length > 0 && !selectedRoleId) {
          setSelectedRoleId(rolesData[0].id);
        }
      } catch (err: any) {
        setError(err?.response?.data?.error || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  useEffect(() => {
    if (!selectedRoleId) return;
    rolesApi.getPermissions(selectedRoleId).then((res) => {
      setCheckedIds(new Set(res.permission_ids));
    }).catch((err: any) => {
      setError(err?.response?.data?.error || 'Failed to load permissions');
    });
  }, [selectedRoleId]);

  const selectedRole = roles.find((r) => r.id === selectedRoleId);

  const grouped = permissions.reduce<Record<string, Permission[]>>((acc, p) => {
    if (!acc[p.module]) acc[p.module] = [];
    acc[p.module].push(p);
    return acc;
  }, {});

  const toggle = (id: number) => {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleModule = (module: string, checked: boolean) => {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      for (const p of grouped[module]) {
        if (checked) next.add(p.id);
        else next.delete(p.id);
      }
      return next;
    });
  };

  const moduleAllChecked = (module: string) =>
    grouped[module].every((p) => checkedIds.has(p.id));

  const handleSave = async () => {
    if (!selectedRoleId) return;
    setSaving(true);
    setError('');
    try {
      await rolesApi.updatePermissions(selectedRoleId, Array.from(checkedIds));
      setSuccess('Permissions updated successfully');
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to update permissions');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader title="Role Permissions" subtitle="Assign permissions to roles" />

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 3, mb: 3, maxWidth: 400 }}>
        <FormControl fullWidth>
          <InputLabel>Select Role</InputLabel>
          <Select
            value={selectedRoleId ?? ''}
            label="Select Role"
            onChange={(e) => setSelectedRoleId(Number(e.target.value))}
          >
            {roles.map((r) => (
              <MenuItem key={r.id} value={r.id}>
                {r.name} {r.is_system ? <Chip label="System" size="small" sx={{ ml: 1 }} /> : ''}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Paper>

      {selectedRole && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            {selectedRole.name}
            {selectedRole.is_system && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                (System role - some permissions cannot be changed)
              </Typography>
            )}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {selectedRole.description}
          </Typography>

          {Object.entries(grouped).map(([module, perms]) => (
            <Box key={module} sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ textTransform: 'capitalize' }}>
                  {module}
                </Typography>
                <FormControlLabel
                  control={
                    <Checkbox
                      size="small"
                      checked={moduleAllChecked(module)}
                      indeterminate={
                        perms.some((p) => checkedIds.has(p.id)) && !moduleAllChecked(module)
                      }
                      onChange={(e) => toggleModule(module, e.target.checked)}
                    />
                  }
                  label="Select All"
                />
              </Box>
              <Divider sx={{ mb: 1 }} />
              <FormGroup sx={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: 0 }}>
                {perms.map((p) => (
                  <FormControlLabel
                    key={p.id}
                    control={
                      <Checkbox
                        checked={checkedIds.has(p.id)}
                        onChange={() => toggle(p.id)}
                        disabled={selectedRole.is_system}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {p.description || p.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {p.name}
                        </Typography>
                      </Box>
                    }
                    sx={{ width: 220, alignItems: 'flex-start', mx: 0, pr: 2 }}
                  />
                ))}
              </FormGroup>
            </Box>
          ))}

          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={saving || selectedRole.is_system}
            >
              {saving ? 'Saving...' : 'Save Permissions'}
            </Button>
            <Button
              variant="outlined"
              onClick={() => setCheckedIds(new Set())}
              disabled={selectedRole.is_system}
            >
              Clear All
            </Button>
          </Box>
        </Paper>
      )}

      <Snackbar open={!!success} autoHideDuration={3000} onClose={() => setSuccess('')}>
        <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>
      </Snackbar>
    </Box>
  );
}
