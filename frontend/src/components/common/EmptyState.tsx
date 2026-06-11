import { Box, Typography } from '@mui/material';
import { Inbox } from '@mui/icons-material';

interface EmptyStateProps {
  message?: string;
}

export default function EmptyState({ message = 'No records found' }: EmptyStateProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8, color: 'text.secondary' }}>
      <Inbox sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
      <Typography>{message}</Typography>
    </Box>
  );
}
