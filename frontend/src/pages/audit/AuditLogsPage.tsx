import { useCallback, useEffect, useState } from 'react';
import {
  Box, TextField, FormControl, InputLabel, Select, MenuItem,
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Table, TableBody, TableCell, TableRow,
} from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { auditApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import { todayStr, monthAgoStr } from '../../utils/format';
import type { AuditLog } from '../../types';

const MODULES = ['auth', 'users', 'branches', 'products', 'customers', 'sales', 'inventory', 'production', 'warehouses', 'transfers', 'settings'];
const ACTIONS = ['create', 'update', 'delete', 'login', 'logout', 'approve', 'cancel', 'issue', 'receive', 'export'];

function DiffTable({ oldValues, newValues }: { oldValues: Record<string, unknown> | null; newValues: Record<string, unknown> | null }) {
  if (!oldValues && !newValues) {
    return <Typography color="text.secondary">No change data available</Typography>;
  }

  const allKeys = new Set([
    ...Object.keys(oldValues || {}),
    ...Object.keys(newValues || {}),
  ]);

  const rows: { key: string; old: string; new: string; changed: boolean }[] = [];
  for (const key of allKeys) {
    const oldVal = oldValues?.[key] !== undefined ? String(oldValues[key]) : '—';
    const newVal = newValues?.[key] !== undefined ? String(newValues[key]) : '—';
    rows.push({ key, old: oldVal, new: newVal, changed: oldVal !== newVal });
  }

  if (rows.length === 0) {
    return <Typography color="text.secondary">No change data available</Typography>;
  }

  return (
    <Table size="small" sx={{ mt: 1 }}>
      <TableBody>
        {rows.map((row) => (
          <TableRow
            key={row.key}
            sx={row.changed ? { bgcolor: '#FFF8E1' } : undefined}
          >
            <TableCell sx={{ fontWeight: 600, width: 160, py: 0.5 }}>{row.key}</TableCell>
            <TableCell
              sx={{
                py: 0.5,
                textDecoration: row.changed ? 'line-through' : undefined,
                color: row.changed ? 'error.main' : 'text.primary',
                bgcolor: row.changed ? '#FFEBEE' : undefined,
              }}
            >
              {row.old}
            </TableCell>
            <TableCell
              sx={{
                py: 0.5,
                fontWeight: row.changed ? 600 : undefined,
                color: row.changed ? 'success.dark' : 'text.primary',
                bgcolor: row.changed ? '#E8F5E9' : undefined,
              }}
            >
              {row.new}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export default function AuditLogsPage() {
  const { user, hasRole } = useAuthStore();
  const canViewAll = hasRole('Owner', 'Auditor', 'General Manager');
  const [data, setData] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);
  const [loading, setLoading] = useState(false);
  const [module, setModule] = useState('');
  const [action, setAction] = useState('');
  const [userSearch, setUserSearch] = useState(user?.username || '');
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (module) params.module = module;
      if (action) params.action = action;
      if (canViewAll) {
        if (userSearch.trim()) params.user_search = userSearch.trim();
      } else {
        params.user_search = user?.username;
      }
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await auditApi.list(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, module, action, userSearch, dateFrom, dateTo, user?.username, canViewAll]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const columns = [
    {
      id: 'timestamp',
      label: 'Timestamp',
      render: (row: AuditLog) => new Date(row.timestamp).toLocaleString(),
    },
    { id: 'username', label: 'User' },
    { id: 'action', label: 'Action' },
    { id: 'module', label: 'Module' },
    { id: 'description', label: 'Description' },
    { id: 'entity_type', label: 'Entity Type' },
    {
      id: 'entity_id',
      label: 'Entity ID',
      render: (row: AuditLog) => row.entity_id ?? '-',
    },
    { id: 'ip_address', label: 'IP Address' },
    {
      id: 'changes',
      label: 'Changes',
      render: (row: AuditLog) =>
        row.old_values || row.new_values ? (
          <Button size="small" variant="outlined" onClick={() => setSelectedLog(row)}>
            View Diff
          </Button>
        ) : (
          '—'
        ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Audit Logs"
        subtitle="System activity and change tracking with before/after values"
      />
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ width: 180 }}>
          <InputLabel>Module</InputLabel>
          <Select
            value={module}
            label="Module"
            onChange={(e) => { setModule(e.target.value); setPage(1); }}
          >
            <MenuItem value="">All</MenuItem>
            {MODULES.map((m) => (
              <MenuItem key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ width: 180 }}>
          <InputLabel>Action</InputLabel>
          <Select
            value={action}
            label="Action"
            onChange={(e) => { setAction(e.target.value); setPage(1); }}
          >
            <MenuItem value="">All</MenuItem>
            {ACTIONS.map((a) => (
              <MenuItem key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</MenuItem>
            ))}
          </Select>
        </FormControl>
        {canViewAll && (
          <TextField
            size="small"
            placeholder="Search user..."
            value={userSearch}
            onChange={(e) => { setUserSearch(e.target.value); setPage(1); }}
            sx={{ width: 200 }}
          />
        )}
        <TextField
          size="small"
          type="date"
          label="From"
          InputLabelProps={{ shrink: true }}
          value={dateFrom}
          onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
          sx={{ width: 180 }}
        />
        <TextField
          size="small"
          type="date"
          label="To"
          InputLabelProps={{ shrink: true }}
          value={dateTo}
          onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
          sx={{ width: 180 }}
        />
      </Box>
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

      <Dialog open={!!selectedLog} onClose={() => setSelectedLog(null)} maxWidth="md" fullWidth>
        <DialogTitle>
          Change Details — {selectedLog?.entity_type || 'N/A'} #{selectedLog?.entity_id || ''}
          <Typography variant="body2" color="text.secondary">
            {selectedLog?.action} by {selectedLog?.username} on{' '}
            {selectedLog?.timestamp ? new Date(selectedLog.timestamp).toLocaleString() : ''}
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="subtitle2" gutterBottom>
            Modified Fields (strikethrough = old, green = new)
          </Typography>
          <DiffTable
            oldValues={selectedLog?.old_values as Record<string, unknown> | null}
            newValues={selectedLog?.new_values as Record<string, unknown> | null}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedLog(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
