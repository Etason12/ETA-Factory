import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Typography, Paper, Grid2 as Grid, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, CircularProgress } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import { salesApi } from '../../api/endpoints';
import type { SalesOrder } from '../../types';
import StatusChip from '../../components/common/StatusChip';
import PageHeader from '../../components/common/PageHeader';
import { formatCurrency } from '../../utils/format';

export default function SalesOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<SalesOrder | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      salesApi.orders.get(Number(id)).then(setOrder).finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) return <CircularProgress />;
  if (!order) return <Typography>Order not found</Typography>;

  return (
    <Box>
      <PageHeader
        title={`Sales Order #${order.order_number}`}
        action={{ label: 'Back to Orders', path: '/sales/orders', icon: <ArrowBackIcon /> }}
      />
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="subtitle2" color="text.secondary">Customer</Typography>
            <Typography variant="body1">{order.customer_name}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="subtitle2" color="text.secondary">Status</Typography>
            <StatusChip status={order.status} />
          </Grid>
        </Grid>
      </Paper>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell align="right">Qty</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {order.items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.product_name}</TableCell>
                <TableCell align="right">{item.quantity}</TableCell>
                <TableCell align="right">{formatCurrency(item.unit_price)}</TableCell>
                <TableCell align="right">{formatCurrency(item.quantity * item.unit_price)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button 
          variant="contained" 
          color="secondary" 
          startIcon={<LocalShippingIcon />}
          onClick={() => navigate('/warehouses/giv', { state: { orderId: order.id } })}
        >
          Generate GIV
        </Button>
      </Box>
    </Box>
  );
}
