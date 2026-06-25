import { Box, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TablePagination, Paper, Tooltip, IconButton, Menu, MenuItem, FormControlLabel, Checkbox } from '@mui/material';
import { ViewColumn, FileDownload } from '@mui/icons-material';
import EmptyState from './EmptyState';
import { useState } from 'react';

interface Column {
  id: string;
  label: string;
  render?: (row: any) => React.ReactNode;
  width?: string | number;
  nowrap?: boolean;
}

interface DataTableProps {
  columns: Column[];
  data: any[];
  loading?: boolean;
  total?: number;
  page?: number;
  perPage?: number;
  onPageChange?: (page: number) => void;
  onPerPageChange?: (perPage: number) => void;
}

export default function DataTable({ columns, data, loading, total = 0, page = 1, perPage = 25, onPageChange, onPerPageChange }: DataTableProps) {
  const [rowsPerPage, setRowsPerPage] = useState(perPage);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [hiddenColumns, setHiddenColumns] = useState<string[]>([]);

  const toggleColumn = (colId: string) => {
    setHiddenColumns(prev => prev.includes(colId) ? prev.filter(c => c !== colId) : [...prev, colId]);
  };

  const visibleColumns = columns.filter(col => !hiddenColumns.includes(col.id));

  const exportCSV = () => {
    const headers = visibleColumns.map(col => col.label);
    const rows = data.map(row =>
      visibleColumns.map(col => {
        const val = col.render ? stripRenderText(col.render(row)) : row[col.id];
        const str = val == null ? '' : String(val);
        return str.includes(',') || str.includes('"') || str.includes('\n') ? `"${str.replace(/"/g, '""')}"` : str;
      })
    );
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const stripRenderText = (node: React.ReactNode): string => {
    if (node == null) return '';
    if (typeof node === 'string') return node;
    if (typeof node === 'number') return String(node);
    if (Array.isArray(node)) return node.map(stripRenderText).join(' ');
    return '';
  };

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <Box sx={{ p: 1, display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
        <Tooltip title="Download CSV">
          <IconButton onClick={exportCSV} size="small">
            <FileDownload />
          </IconButton>
        </Tooltip>
        <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small">
          <ViewColumn />
        </IconButton>
        <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={() => setAnchorEl(null)}>
          {columns.map(col => (
            <MenuItem key={col.id} dense>
              <FormControlLabel 
                control={<Checkbox checked={!hiddenColumns.includes(col.id)} onChange={() => toggleColumn(col.id)} size="small"/>}
                label={col.label}
              />
            </MenuItem>
          ))}
        </Menu>
      </Box>
      <TableContainer>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {visibleColumns.map((col) => (
                    <TableCell key={col.id} sx={{ fontWeight: 600, width: col.width, whiteSpace: col.nowrap ? 'nowrap' : undefined }}>
                      {col.label}
                    </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={visibleColumns.length} align="center" sx={{ py: 4 }}>
                  <CircularProgress size={32} />
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={visibleColumns.length} align="center">
                  <EmptyState />
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, i) => (
                <TableRow key={row.id || i} hover>
                  {visibleColumns.map((col) => (
                    <TableCell key={col.id} sx={{ whiteSpace: col.nowrap ? 'nowrap' : undefined }}>
                      {col.render ? col.render(row) : row[col.id] ?? '-'}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      {onPageChange && (
        <TablePagination
          component="div"
          count={total}
          page={page - 1}
          rowsPerPage={rowsPerPage}
          onPageChange={(_, p) => onPageChange(p + 1)}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); onPerPageChange?.(parseInt(e.target.value, 10)); }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      )}
    </Paper>
  );
}
