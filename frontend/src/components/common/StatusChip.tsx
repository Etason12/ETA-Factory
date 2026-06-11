import { Chip } from '@mui/material';

const statusColors: Record<string, string> = {
  Draft: 'default',
  Pending: 'warning',
  'Pending Approval': 'warning',
  Approved: 'success',
  'In Transit': 'info',
  Received: 'success',
  Cancelled: 'error',
  Active: 'success',
  Unpaid: 'error',
  Paid: 'success',
  Partial: 'warning',
  Completed: 'success',
  Converted: 'info',
};

interface StatusChipProps {
  status: string;
}

export default function StatusChip({ status }: StatusChipProps) {
  const color = (statusColors[status] || 'default') as any;
  return <Chip label={status} color={color} size="small" variant="outlined" />;
}
