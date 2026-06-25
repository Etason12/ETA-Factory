import { useCallback, useEffect, useState } from 'react';
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, TextField,
  MenuItem, IconButton, Tooltip, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Typography, Paper, Grid2 as Grid,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import DataTable from '../../components/common/DataTable';
import DateRangeFilter from '../../components/common/DateRangeFilter';
import StatusChip from '../../components/common/StatusChip';
import { warehousesApi, productsApi } from '../../api/endpoints';
import { blurActiveElement } from '../../utils/focus';
import { useAuthStore } from '../../store/authStore';
import { todayStr, monthAgoStr } from '../../utils/format';
import type { DisposalVoucher, DisposalVoucherItem, Warehouse, Product } from '../../types';

interface LineItem {
  product_id: number;
  product_name: string;
  quantity: number;
  reason: string;
}

const disposalReasons = [
  'Damaged',
  'Expired',
  'Obsolete',
  'Lost',
  'Theft',
  'Quality Issue',
  'Other',
];

export default function DisposalVoucherPage() {
  const { hasRole } = useAuthStore();
  const canCreate = hasRole('Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper');
  const canApprove = hasRole('Owner', 'General Manager', 'Warehouse Manager');
  const [approveTarget, setApproveTarget] = useState<DisposalVoucher | null>(null);
  const [data, setData] = useState<DisposalVoucher[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);
  const [formOpen, setFormOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailDV, setDetailDV] = useState<DisposalVoucher | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [stock, setStock] = useState<Record<number, number>>({});

  const fetchStock = async (warehouseId: number) => {
    try {
      const inv = await warehousesApi.inventory(warehouseId);
      const stockMap = inv.reduce((acc: Record<number, number>, item: any) => ({ ...acc, [item.product_id]: item.quantity_on_hand }), {} as Record<number, number>);
      setStock(stockMap);
    } catch {
      setStock({});
    }
  };

  const [form, setForm] = useState({
    warehouse_id: 0,
    voucher_date: todayStr,
    reason: '',
    notes: '',
  });
  const [lineItems, setLineItems] = useState<LineItem[]>([]);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, per_page: perPage };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await warehousesApi.disposalList(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, dateFrom, dateTo]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this disposal voucher?')) return;
    try {
      await warehousesApi.deleteDisposal(id);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.message || 'Failed to delete');
    }
  };

  useEffect(() => { fetch(); }, [fetch]);

  useEffect(() => {
    if (formOpen) {
      Promise.all([
        warehousesApi.list({ per_page: 1000 }),
        productsApi.list({ per_page: 1000 }),
      ]).then(([wRes, pRes]) => {
        setWarehouses(wRes.items);
        setProducts(pRes.items);
      });
    }
  }, [formOpen]);

  const handleViewDetail = async (dv: DisposalVoucher) => {
    try {
      const full = await warehousesApi.getDisposal(dv.id);
      setDetailDV(full);
    } catch {
      setDetailDV(dv);
    }
    setDetailOpen(true);
  };

  const addLineItem = () => {
    setLineItems([...lineItems, { product_id: 0, product_name: '', quantity: 1, reason: '' }]);
  };

  const removeLineItem = (idx: number) => {
    setLineItems(lineItems.filter((_, i) => i !== idx));
  };

  const updateLineItem = (idx: number, field: string, value: unknown) => {
    const items = [...lineItems];
    (items[idx] as any)[field] = value;
    if (field === 'product_id') {
      const p = products.find((pr) => pr.id === value);
      if (p) items[idx].product_name = p.name;
    }
    setLineItems(items);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.warehouse_id || !form.reason || lineItems.length === 0 || !lineItems.some((l) => l.product_id)) {
      alert('Please fill warehouse, reason, and at least one product item');
      return;
    }
    setSubmitting(true);
    try {
      await warehousesApi.createDisposal({
        ...form,
        voucher_number: `DSP-${Date.now()}`,
        items: lineItems.map((l) => ({
          product_id: l.product_id,
          quantity: l.quantity,
          reason: l.reason || undefined,
        })),
      });
      blurActiveElement();
      setFormOpen(false);
      setForm({ warehouse_id: 0, voucher_date: todayStr, reason: '', notes: '' });
      setLineItems([]);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Failed to create disposal voucher');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!approveTarget) return;
    try {
      await warehousesApi.approveDisposal(approveTarget.id);
      blurActiveElement();
      setApproveTarget(null);
      fetch();
    } catch (err: any) {
      alert(err?.response?.data?.message || err?.response?.data?.error || 'Failed to approve disposal voucher');
    }
  };

  const columns = [
    { id: 'voucher_number', label: 'Voucher #' },
    { id: 'warehouse_name', label: 'Warehouse' },
    { id: 'voucher_date', label: 'Date' },
    { id: 'reason', label: 'Reason' },
    { id: 'created_by_name', label: 'Created By' },
    { id: 'disposed_by_name', label: 'Disposed By' },
    {
      id: 'status', label: 'Status',
      render: (row: DisposalVoucher) => <StatusChip status={row.status} />,
    },
    {
      id: 'actions', label: 'Actions', width: 160,
      render: (row: DisposalVoucher) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="View Details">
            <IconButton size="small" onClick={() => handleViewDetail(row)}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {row.status === 'Draft' && canApprove && (
            <Tooltip title="Approve Disposal">
              <IconButton size="small" color="success" onClick={() => setApproveTarget(row)}>
                <CheckCircleIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {row.status === 'Draft' && (
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
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4">Disposal Vouchers</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Record disposed / written-off goods from warehouse
          </Typography>
        </Box>
        {canCreate && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setFormOpen(true)}>
            New Disposal
          </Button>
        )}
      </Box>
      <Box sx={{ mb: 2 }}>
        <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={(v) => { setDateFrom(v); setPage(1); }} onDateToChange={(v) => { setDateTo(v); setPage(1); }} />
      </Box>
      <DataTable
        columns={columns} data={data} loading={loading} total={total}
        page={page} perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={(pp) => { setPerPage(pp); setPage(1); }}
      />

      <Dialog open={formOpen} onClose={() => { blurActiveElement(); setFormOpen(false); setLineItems([]); }} maxWidth="md" fullWidth disableRestoreFocus>
        <Box component="form" onSubmit={handleCreate}>
          <DialogTitle>New Disposal Voucher</DialogTitle>
          <DialogContent>
            <Grid container spacing={2.5} sx={{ pt: 2 }}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Warehouse *" select fullWidth value={form.warehouse_id}
                  onChange={(e) => {
                    const wId = Number(e.target.value);
                    setForm({ ...form, warehouse_id: wId });
                    fetchStock(wId);
                  }}>
                  <MenuItem value={0} disabled>Select warehouse</MenuItem>
                  {warehouses.map((w) => (
                    <MenuItem key={w.id} value={w.id}>{w.name} ({w.code})</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Voucher Date" type="date" fullWidth value={form.voucher_date}
                  onChange={(e) => setForm({ ...form, voucher_date: e.target.value })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Disposal Reason *" select fullWidth value={form.reason}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}>
                  <MenuItem value="" disabled>Select reason</MenuItem>
                  {disposalReasons.map((r) => (
                    <MenuItem key={r} value={r}>{r}</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Notes" fullWidth value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </Grid>
              <Grid size={12}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Line Items</Typography>
                {lineItems.map((item, idx) => (
                  <Box key={idx} sx={{ display: 'flex', gap: 2, mb: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
                    <TextField select label="Product" size="small" sx={{ flex: 2, minWidth: 180 }}
                      value={item.product_id}
                      onChange={(e) => updateLineItem(idx, 'product_id', Number(e.target.value))}>
                      <MenuItem value={0} disabled>Select product</MenuItem>
                      {products.map((p) => (
                        <MenuItem key={p.id} value={p.id}>{p.name} ({p.sku})</MenuItem>
                      ))}
                    </TextField>
                    <TextField label="Qty" type="number" size="small" sx={{ flex: 1, minWidth: 100 }}
                      value={item.quantity}
                      error={item.product_id > 0 && item.quantity > (stock[item.product_id] || 0)}
                      helperText={item.product_id > 0 && item.quantity > (stock[item.product_id] || 0) ? `Max: ${stock[item.product_id] || 0}` : ''}
                      onChange={(e) => updateLineItem(idx, 'quantity', Number(e.target.value))}
                      slotProps={{ htmlInput: { min: 1 } }} />
                    <TextField select label="Item Reason" size="small" sx={{ flex: 1, minWidth: 140 }}
                      value={item.reason}
                      onChange={(e) => updateLineItem(idx, 'reason', e.target.value)}>
                      <MenuItem value="">Same as voucher</MenuItem>
                      {disposalReasons.map((r) => (
                        <MenuItem key={r} value={r}>{r}</MenuItem>
                      ))}
                    </TextField>
                    <IconButton color="error" onClick={() => removeLineItem(idx)}>
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                ))}
                <Button size="small" startIcon={<AddIcon />} onClick={addLineItem} sx={{ mt: 1 }}>
                  Add Item
                </Button>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { blurActiveElement(); setFormOpen(false); setLineItems([]); }}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save Disposal'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={!!approveTarget} onClose={() => { blurActiveElement(); setApproveTarget(null); }} disableRestoreFocus>
        <DialogTitle>Confirm Approval</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to approve disposal voucher <strong>{approveTarget?.voucher_number}</strong>?
            This will deduct the disposed quantities from inventory.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApproveTarget(null)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleApprove}>Approve</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={detailOpen} onClose={() => { blurActiveElement(); setDetailOpen(false); }} maxWidth="sm" fullWidth disableRestoreFocus>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{detailDV?.voucher_number}</span>
          <IconButton size="small" onClick={() => setDetailOpen(false)}><CloseIcon /></IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">Warehouse: {detailDV?.warehouse_name}</Typography>
            <Typography variant="body2" color="text.secondary">Date: {detailDV?.voucher_date}</Typography>
            <Typography variant="body2" color="text.secondary">Reason: {detailDV?.reason}</Typography>
            <Typography variant="body2" color="text.secondary">Status: {detailDV?.status}</Typography>
            {detailDV?.created_by_name && <Typography variant="body2" color="text.secondary">Created By: {detailDV.created_by_name}</Typography>}
            {detailDV?.disposed_by_name && <Typography variant="body2" color="text.secondary">Disposed By: {detailDV.disposed_by_name}</Typography>}
            {detailDV?.notes && <Typography variant="body2" color="text.secondary">Notes: {detailDV.notes}</Typography>}
          </Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Items</Typography>
          {detailDV?.items && detailDV.items.length > 0 ? (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Product</TableCell>
                      <TableCell sx={{ fontWeight: 600 }} align="right">Qty</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Reason</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                  {detailDV.items.map((item: DisposalVoucherItem) => (
                    <TableRow key={item.id} hover>
                      <TableCell>{item.product_name}</TableCell>
                      <TableCell align="right">{item.quantity}</TableCell>
                      <TableCell>{item.reason || detailDV.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography color="text.secondary">No items</Typography>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
