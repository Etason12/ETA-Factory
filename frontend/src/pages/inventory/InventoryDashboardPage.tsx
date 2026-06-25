import { useEffect, useState } from 'react';
import {
  Box, Paper, Typography, Grid2 as Grid, Chip, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, CircularProgress, useTheme,
} from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import InventoryIcon from '@mui/icons-material/Inventory';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import MoveUpIcon from '@mui/icons-material/MoveUp';
import PageHeader from '../../components/common/PageHeader';
import { inventoryApi } from '../../api/endpoints';

interface Summary {
  total_products: number;
  total_warehouses: number;
  total_inventory_items: number;
  total_quantity_on_hand: number;
  total_reserved_quantity: number;
  low_stock_count: number;
  recent_movements: any[];
  warehouse_data: { name: string; value: number }[];
  stock_status: { name: string; value: number }[];
}

export default function InventoryDashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    inventoryApi.summary().then(setSummary).finally(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;

  if (!summary) return <Typography color="error">Failed to load summary</Typography>;

  const cards = [
    { label: 'Active Products', value: summary.total_products, icon: <InventoryIcon />, color: '#1976d2' },
    { label: 'Warehouses', value: summary.total_warehouses, icon: <WarehouseIcon />, color: '#388e3c' },
    { label: 'Total Qty On Hand', value: (summary.total_quantity_on_hand ?? 0).toLocaleString(), icon: <MoveUpIcon />, color: '#f57c00' },
    { label: 'Low Stock Items', value: summary.low_stock_count ?? 0, icon: <WarningAmberIcon />, color: (summary.low_stock_count ?? 0) > 0 ? '#d32f2f' : '#388e3c' },
  ];

  const movements = summary.recent_movements || [];

  return (
    <Box>
      <PageHeader title="Inventory Dashboard" subtitle="Overview of stock levels and movements" />
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {cards.map((card) => (
          <Grid key={card.label} size={{ xs: 12, sm: 6, md: 3 }}>
            <Paper sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2, borderRadius: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${card.color}15`, color: card.color, display: 'flex' }}>
                {card.icon}
              </Box>
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>{card.value}</Typography>
                <Typography variant="body2" color="text.secondary">{card.label}</Typography>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {(summary.low_stock_count ?? 0) > 0 && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: '#fff3e0', borderRadius: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningAmberIcon color="warning" />
          <Typography>{summary.low_stock_count ?? 0} item(s) below minimum stock level. <Chip label="View Low Stock" size="small" color="warning" component="a" href="/inventory/low-stock" clickable sx={{ ml: 1 }} /></Typography>
        </Paper>
      )}

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3, borderRadius: 2, height: 400 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Stock Distribution by Warehouse</Typography>
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={summary.warehouse_data || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#1976d2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3, borderRadius: 2, height: 400 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Stock Health</Typography>
            <ResponsiveContainer width="100%" height={340}>
              <PieChart>
                <Pie
                  data={summary.stock_status || []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  <Cell fill="#388e3c" />
                  <Cell fill="#d32f2f" />
                </Pie>
                <RechartsTooltip />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ borderRadius: 2 }}>
        <Typography variant="h6" sx={{ p: 2, pb: 1 }}>Recent Inventory Movements</Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Product</TableCell>
                <TableCell>Warehouse</TableCell>
                <TableCell>Type</TableCell>
                <TableCell align="right">Qty</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {movements.length === 0 ? (
                <TableRow><TableCell colSpan={5} align="center">No recent movements</TableCell></TableRow>
              ) : movements.map((m: any) => (
                <TableRow key={m.id}>
                  <TableCell>{m.transaction_date ? new Date(m.transaction_date).toLocaleDateString() : '-'}</TableCell>
                  <TableCell>{m.product_name || m.product_sku}</TableCell>
                  <TableCell>{m.warehouse_name}</TableCell>
                  <TableCell><Chip label={m.movement_type} size="small" variant="outlined" /></TableCell>
                  <TableCell align="right" sx={{ color: m.quantity < 0 ? 'error.main' : 'success.main', fontWeight: 600 }}>
                    {m.quantity > 0 ? '+' : ''}{m.quantity}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}