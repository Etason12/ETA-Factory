import { Box, TextField } from '@mui/material';

interface DateRangeFilterProps {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (val: string) => void;
  onDateToChange: (val: string) => void;
}

export default function DateRangeFilter({ dateFrom, dateTo, onDateFromChange, onDateToChange }: DateRangeFilterProps) {
  return (
    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
      <TextField
        label="From"
        type="date"
        size="small"
        value={dateFrom}
        onChange={(e) => onDateFromChange(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
        sx={{ maxWidth: 170 }}
      />
      <TextField
        label="To"
        type="date"
        size="small"
        value={dateTo}
        onChange={(e) => onDateToChange(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
        sx={{ maxWidth: 170 }}
      />
    </Box>
  );
}
