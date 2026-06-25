import { useCallback, useEffect, useState } from 'react';
import { Box, TextField, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import { inventoryApi } from '../../api/endpoints';
import type { InventoryLedger } from '../../types';
import { formatCurrency, todayStr, monthAgoStr } from '../../utils/format';

const MOVEMENT_TYPE_OPTIONS = [
  { value: 'in', label: 'Stock In' },
  { value: 'out', label: 'Stock Out' },
  { value: 'adjustment', label: 'Stock Adjustment' },
];

function getMovementLabel(movement_type: string, reference_type: string | null | undefined): string {
  if (movement_type === 'Opening Balance') return 'Opening Balance';
  if (movement_type === 'Addition') return 'Stock Adjustment (+)';
  if (movement_type === 'Reduction') return 'Stock Adjustment (-)';
  if (movement_type === 'Return') return 'Stock Return';

  const ref = reference_type || '';
  if (movement_type === 'GRV' || movement_type === 'Receipt') {
    if (ref === 'ProductionBatch') return 'Production';
    if (ref === 'Transfer') return 'Transfer In';
    if (ref === 'GRV' || !ref) return 'Goods Received';
    return ref;
  }
  if (movement_type === 'GIV' || movement_type === 'Issue') {
    if (ref === 'Transfer') return 'Transfer Out';
    if (ref === 'LoadingAuthorization') return 'Sales Issue';
    if (ref === 'GIV' || !ref) return 'Goods Issued';
    return ref;
  }
  return movement_type;
}

export default function InventoryLedgerPage() {
  const [data, setData] = useState<InventoryLedger[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [productSearch, setProductSearch] = useState('');
  const [warehouseSearch, setWarehouseSearch] = useState('');
  const [movementType, setMovementType] = useState('');
  const [dateFrom, setDateFrom] = useState(monthAgoStr);
  const [dateTo, setDateTo] = useState(todayStr);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (productSearch.trim()) params.product_search = productSearch.trim();
      if (warehouseSearch.trim()) params.warehouse_search = warehouseSearch.trim();
      if (movementType) params.movement_type = movementType;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await inventoryApi.ledger(params);
      setData(res.items || []);
      setTotal(res.total || 0);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, productSearch, warehouseSearch, movementType, dateFrom, dateTo]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const columns = [
    { id: 'product_name', label: 'Product' },
    { id: 'warehouse_name', label: 'Warehouse' },
    {
      id: 'movement_type',
      label: 'Movement Type',
      render: (row: InventoryLedger) => getMovementLabel(row.movement_type, row.reference_type),
    },
    {
      id: 'quantity',
      label: 'Quantity',
      render: (row: InventoryLedger) => Number(row.quantity).toLocaleString(),
    },
    {
      id: 'unit_cost',
      label: 'Unit Cost',
      render: (row: InventoryLedger) => (row.unit_cost != null ? formatCurrency(Number(row.unit_cost)) : '-'),
    },
    { id: 'reference_type', label: 'Reference Type' },
    {
      id: 'reference_id',
      label: 'Reference ID',
      render: (row: InventoryLedger) => row.reference_id ?? '-',
    },
    { id: 'batch_number', label: 'Batch' },
    {
      id: 'transaction_date',
      label: 'Date',
      render: (row: InventoryLedger) => new Date(row.transaction_date).toLocaleString(),
    },
  ];

  return (
    <>
      <PageHeader
        title="Inventory Ledger"
        subtitle="Movement history of inventory items"
      />
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search product..."
          value={productSearch}
          onChange={(e) => { setProductSearch(e.target.value); setPage(1); }}
          sx={{ width: 200 }}
        />
        <TextField
          size="small"
          placeholder="Search warehouse..."
          value={warehouseSearch}
          onChange={(e) => { setWarehouseSearch(e.target.value); setPage(1); }}
          sx={{ width: 200 }}
        />
        <FormControl size="small" sx={{ width: 180 }}>
          <InputLabel>Movement Type</InputLabel>
          <Select
            value={movementType}
            label="Movement Type"
            onChange={(e) => { setMovementType(e.target.value); setPage(1); }}
          >
            <MenuItem value="">All</MenuItem>
            {MOVEMENT_TYPE_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
            ))}
          </Select>
        </FormControl>
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
