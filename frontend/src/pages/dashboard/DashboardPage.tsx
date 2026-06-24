import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box, Card, CardContent, Typography, Grid2 as Grid, Skeleton, Alert, Avatar, Button, Paper,
  List, ListItem, ListItemText, Divider, useMediaQuery, useTheme,
} from '@mui/material';
import {
  LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, CartesianGrid,
  BarChart, Bar, PieChart, Pie, Cell, Legend,
} from 'recharts';

import InventoryIcon from '@mui/icons-material/Inventory';
import PeopleIcon from '@mui/icons-material/People';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import WarningIcon from '@mui/icons-material/Warning';
import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing';
import AddIcon from '@mui/icons-material/Add';
import ReceiptIcon from '@mui/icons-material/Receipt';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import dayjs from 'dayjs';
import { productsApi, customersApi, salesApi, transfersApi, productionApi, auditApi } from '../../api/endpoints';
import PageHeader from '../../components/common/PageHeader';
import type { AuditLog } from '../../types';
import { formatCurrency } from '../../utils/format';

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
  loading?: boolean;
}

function StatCard({ icon, label, value, color, loading }: StatCardProps) {
  return (
    <Card>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, '&:last-child': { pb: 2 } }}>
        <Avatar sx={{ bgcolor: `${color}.main`, width: 48, height: 48 }}>
          {icon}
        </Avatar>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {loading ? (
            <>
              <Skeleton width={80} height={30} />
              <Skeleton width={100} height={20} />
            </>
          ) : (
            <>
              <Typography variant="h5" fontWeight={600}>
                {value}
              </Typography>
              <Typography variant="body2" color="text.secondary" noWrap>
                {label}
              </Typography>
            </>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

const quickActions = [
  { label: 'New Product', path: '/products/new', icon: <AddIcon /> },
  { label: 'New Customer', path: '/customers/new', icon: <PeopleIcon /> },
  { label: 'Sales Order', path: '/sales/orders/new', icon: <ShoppingCartIcon /> },
  { label: 'Production Batch', path: '/production/batches/new', icon: <PrecisionManufacturingIcon /> },
  { label: 'New Transfer', path: '/transfers/new', icon: <AccountTreeIcon /> },
  { label: 'GRV Entry', path: '/warehouses/grv', icon: <ReceiptIcon /> },
];


const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export default function DashboardPage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const [products, customers, orders, transfers, production, audit, revenue, trend, orderStats, prodTrend] = await Promise.all([
        productsApi.list({ per_page: 1 }).catch(() => ({ items: [], total: 0 })),
        customersApi.list({ per_page: 1 }).catch(() => ({ items: [], total: 0 })),
        salesApi.orders.list({ per_page: 1 }).catch(() => ({ items: [], total: 0 })),
        transfersApi.list({ per_page: 1 }).catch(() => ({ items: [], total: 0 })),
        productionApi.list({ per_page: 1 }).catch(() => ({ items: [], total: 0 })),
        auditApi.list({ per_page: 5 }).catch(() => ({ items: [], total: 0 })),
        salesApi.getRevenue().catch(() => ({ total_revenue: 0 })),
        salesApi.getRevenueTrend().catch(() => []),
        salesApi.orders.list({ per_page: 100 }).catch(() => ({ items: [] })),
        productionApi.list({ per_page: 20 }).catch(() => ({ items: [] })),
      ]);
      const revenueData = trend.length > 0 ? trend : MONTHS.map((name) => ({ name, revenue: 0 }));
      const statusCounts: Record<string, number> = {};
      for (const o of orderStats.items || []) {
        const s = (o as unknown as Record<string, unknown>).status as string || 'Unknown';
        statusCounts[s] = (statusCounts[s] || 0) + 1;
      }
      const orderStatusData = Object.entries(statusCounts).map(([name, value]) => ({ name, value }));
      const prodByMonth: Record<string, number> = {};
      for (const b of prodTrend.items || []) {
        const date = (b as unknown as Record<string, unknown>).created_at as string;
        if (date) {
          const m = dayjs(date).format('MMM');
          prodByMonth[m] = (prodByMonth[m] || 0) + 1;
        }
      }
      const productionTrendData = MONTHS.map((name) => ({ name, batches: prodByMonth[name] || 0 }));
      return {
        total_products: products.total,
        total_customers: customers.total,
        active_orders: orders.total,
        total_revenue: revenue.total_revenue,
        pending_transfers: transfers.total,
        low_stock_items: 0,
        production_batches: production.total,
        recentActivity: audit.items as AuditLog[],
        revenueData,
        orderStatusData,
        productionTrendData,
      };
    },
  });

  const stats: Omit<StatCardProps, 'loading'>[] = [
    { icon: <InventoryIcon />, label: 'Total Products', value: data?.total_products ?? 0, color: 'primary' },
    { icon: <PeopleIcon />, label: 'Total Customers', value: data?.total_customers ?? 0, color: 'secondary' },
    { icon: <ShoppingCartIcon />, label: 'Active Orders', value: data?.active_orders ?? 0, color: 'success' },
    { icon: <AttachMoneyIcon />, label: 'Total Revenue', value: formatCurrency(data?.total_revenue ?? 0), color: 'warning' },
    { icon: <LocalShippingIcon />, label: 'Pending Transfers', value: data?.pending_transfers ?? 0, color: 'info' },
    { icon: <WarningIcon />, label: 'Low Stock Items', value: data?.low_stock_items ?? 0, color: 'error' },
    { icon: <PrecisionManufacturingIcon />, label: 'Production Batches', value: data?.production_batches ?? 0, color: 'secondary' },
  ];

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Overview of your factory operations" />
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load dashboard data. Please try again.
        </Alert>
      )}
      <Grid container spacing={4}>
        {stats.map((stat, i) => (
          <Grid key={i} size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard {...stat} loading={isLoading} />
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 3, mt: 5 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Revenue Trend</Typography>
        <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data?.revenueData ?? []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="revenue" stroke={theme.palette.primary.main} strokeWidth={3} />
                </LineChart>
            </ResponsiveContainer>
        </Box>
      </Paper>

      <Grid container spacing={4} sx={{ mt: 1 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Order Status Breakdown</Typography>
            <Box sx={{ height: 280 }}>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={data?.orderStatusData ?? []}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {(data?.orderStatusData ?? []).map((_, i) => (
                      <Cell key={i} fill={[theme.palette.primary.main, theme.palette.success.main, theme.palette.warning.main, theme.palette.error.main, theme.palette.info.main][i % 5]} />
                    ))}
                  </Pie>
                  <Legend />
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Production Batches by Month</Typography>
            <Box sx={{ height: 280 }}>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data?.productionTrendData ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis allowDecimals={false} />
                  <RechartsTooltip />
                  <Bar dataKey="batches" fill={theme.palette.secondary.main} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ mt: 5, mb: 3 }}>
        Quick Actions
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 5 }}>
        {quickActions.map((action) => (
          <Button
            key={action.path}
            variant="outlined"
            startIcon={action.icon}
            onClick={() => navigate(action.path)}
            size={isMobile ? 'small' : 'medium'}
            sx={{ px: isMobile ? 2 : 3, py: 1 }}
          >
            {action.label}
          </Button>
        ))}
      </Box>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Recent Activity
      </Typography>
      <Paper sx={{ overflow: 'hidden', p: 1 }}>
        {isLoading ? (
          <Box sx={{ p: 2 }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} height={40} sx={{ mb: 0.5 }} />
            ))}
          </Box>
        ) : data?.recentActivity?.length ? (
          <List dense disablePadding>
            {data.recentActivity.map((log, i) => (
              <Box key={log.id}>
                {i > 0 && <Divider component="li" />}
                <ListItem>
                  <ListItemText
                    primary={`${log.action} - ${log.module}`}
                    secondary={
                      <>
                        {log.description && `${log.description} `}
                        {log.username ? `by ${log.username} ` : ''}
                        {dayjs(log.timestamp).format('MMM D, YYYY h:mm A')}
                      </>
                    }
                    primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              </Box>
            ))}
          </List>
        ) : (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">No recent activity</Typography>
          </Box>
        )}
      </Paper>
    </>
  );
}
