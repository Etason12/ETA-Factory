import { useCallback, useEffect, useState } from 'react';
import { Box, TextField, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { auditApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import type { AuditLog } from '../../types';

const MODULES = ['auth', 'users', 'branches', 'products', 'customers', 'sales', 'inventory', 'production', 'warehouses', 'transfers', 'settings'];
const ACTIONS = ['create', 'update', 'delete', 'login', 'logout', 'approve', 'cancel', 'issue', 'receive', 'export'];

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
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

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
      setData(res.items);
      setTotal(res.total);
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
  ];

  return (
    <>
      <PageHeader
        title="Audit Logs"
        subtitle="System activity and change tracking"
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
    </>
  );
}
