import { useState, useEffect, useMemo } from 'react';
import { Box, TextField } from '@mui/material';
import { Search } from '@mui/icons-material';
import { inventoryApi } from '../../api/endpoints';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';

export default function LedgerReconciliationReportPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any[]>([]);
  const [search, setSearch] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [inv, ledger] = await Promise.all([
        inventoryApi.list({ per_page: 10000 }),
        inventoryApi.ledger({ per_page: 100000 })
      ]);
      const ledgerMap = (ledger.items || []).reduce((acc, entry) => {
        acc[entry.product_id] = (acc[entry.product_id] || 0) + entry.quantity;
        return acc;
      }, {} as Record<number, number>);
      setData((inv.items || []).map((i: any) => ({
        product_id: i.product_id,
        product_name: i.product_name,
        sku: i.sku || '',
        warehouse_name: i.warehouse_name,
        quantity_on_hand: i.quantity_on_hand,
        ledgerSum: ledgerMap[i.product_id] || 0,
        discrepancy: (i.quantity_on_hand || 0) - (ledgerMap[i.product_id] || 0),
      })));
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const filteredData = useMemo(() => {
    if (!search) return data;
    const q = search.toLowerCase();
    return data.filter(row =>
      (row.product_name || '').toLowerCase().includes(q) ||
      (row.sku || '').toLowerCase().includes(q) ||
      (row.warehouse_name || '').toLowerCase().includes(q)
    );
  }, [data, search]);

  const columns = [
    { id: 'product_name', label: 'Product' },
    { id: 'sku', label: 'SKU' },
    { id: 'warehouse_name', label: 'Warehouse' },
    { id: 'quantity_on_hand', label: 'Inventory Qty' },
    { id: 'ledgerSum', label: 'Ledger Sum' },
    {
      id: 'discrepancy', label: 'Discrepancy',
      render: (row: any) => (
        <Box component="span" sx={{ color: row.discrepancy !== 0 ? 'error.main' : 'success.main', fontWeight: 600 }}>
          {row.discrepancy}
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader title="Ledger Reconciliation Report" subtitle="Compare system stock vs ledger sum" />
      <Box sx={{ mb: 2 }}>
        <TextField
          size="small"
          placeholder="Search by product, SKU, or warehouse..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          slotProps={{ input: { startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> } }}
          sx={{ minWidth: 320 }}
        />
      </Box>
      <DataTable
        columns={columns}
        data={filteredData}
        loading={loading}
        total={filteredData.length}
      />
    </Box>
  );
}
