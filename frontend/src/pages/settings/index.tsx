import { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Divider, TextField, Button,
  Grid2 as Grid, Alert, Snackbar, Switch, FormControlLabel, Chip,
  List, ListItem, ListItemIcon, ListItemText, Avatar, Paper,
  CircularProgress,
} from '@mui/material';
import BusinessIcon from '@mui/icons-material/Business';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import StorageIcon from '@mui/icons-material/Storage';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PaletteIcon from '@mui/icons-material/Palette';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import PageHeader from '../../components/common/PageHeader';
import { authApi } from '../../api/endpoints';
import { useAuthStore } from '../../store/authStore';
import { useCompanyStore } from '../../store/companyStore';
import apiClient from '../../api/client';

export default function SettingsPage() {
  const { user } = useAuthStore();

  // Password change state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdError, setPwdError] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState(false);

  // API health state
  const [apiStatus, setApiStatus] = useState<'idle' | 'checking' | 'ok' | 'error'>('idle');
  const [apiLatency, setApiLatency] = useState<number | null>(null);

  // Company state
  const { company, updateCompany, fetchCompany } = useCompanyStore();
  const { hasRole } = useAuthStore();
  const isOwner = hasRole('Owner');
  const [companyForm, setCompanyForm] = useState<Record<string, string>>({});
  const [companyLoading, setCompanyLoading] = useState(false);
  const [companySuccess, setCompanySuccess] = useState(false);
  const [companyError, setCompanyError] = useState('');

  useEffect(() => {
    fetchCompany();
  }, []);

  useEffect(() => {
    if (company) {
      setCompanyForm({
        name: company.name || '',
        legal_name: company.legal_name || '',
        tax_id: company.tax_id || '',
        address: company.address || '',
        phone: company.phone || '',
        email: company.email || '',
        website: company.website || '',
        currency: company.currency || 'ETB',
        fiscal_year_start: company.fiscal_year_start || '07-01',
      });
    }
  }, [company]);

  const handleCompanyUpdate = async () => {
    setCompanyLoading(true);
    setCompanyError('');
    try {
      await updateCompany(companyForm);
      setCompanySuccess(true);
    } catch (err: any) {
      setCompanyError(err?.response?.data?.error || err?.response?.data?.detail || 'Failed to update company');
    } finally {
      setCompanyLoading(false);
    }
  };

  // Theme preference (stored in localStorage)
  const [denseMode, setDenseMode] = useState(() => localStorage.getItem('denseMode') === 'true');

  // Backup / restore state
  const [backupLoading, setBackupLoading] = useState(false);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [backupMsg, setBackupMsg] = useState('');
  const [backupError, setBackupError] = useState('');

  // Reset database state
  const [resetKeepUsers, setResetKeepUsers] = useState(true);
  const [resetKeepBranches, setResetKeepBranches] = useState(true);
  const [resetKeepCompany, setResetKeepCompany] = useState(true);
  const [resetKeepProducts, setResetKeepProducts] = useState(false);
  const [resetKeepCustomers, setResetKeepCustomers] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMsg, setResetMsg] = useState('');
  const [resetError, setResetError] = useState('');
  const [resetConfirm, setResetConfirm] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPwdError('New passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      setPwdError('New password must be at least 6 characters');
      return;
    }
    setPwdLoading(true);
    setPwdError('');
    try {
      await authApi.changePassword({ old_password: oldPassword, new_password: newPassword });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPwdSuccess(true);
    } catch (err: any) {
      setPwdError(err?.response?.data?.error || err?.response?.data?.detail || 'Failed to change password. Check your current password.');
    } finally {
      setPwdLoading(false);
    }
  };

  const handleCheckApi = async () => {
    setApiStatus('checking');
    setApiLatency(null);
    const start = performance.now();
    try {
      await apiClient.get('/auth/me');
      const latency = Math.round(performance.now() - start);
      setApiLatency(latency);
      setApiStatus('ok');
    } catch {
      setApiStatus('error');
    }
  };

  const handleDenseModeToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.checked;
    setDenseMode(val);
    localStorage.setItem('denseMode', String(val));
  };

  const handleBackup = async () => {
    setBackupLoading(true);
    setBackupMsg('');
    setBackupError('');
    try {
      const resp = await apiClient.get('/company/backup', { responseType: 'blob' });
      const blob = new Blob([resp.data], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const disposition = resp.headers['content-disposition'];
      const match = disposition?.match(/filename=(.+)/);
                    a.download = match?.[1] || `selam_terranite_backup_${new Date().toISOString().slice(0,10)}.db`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setBackupMsg('Backup downloaded successfully');
    } catch (err: any) {
      setBackupError(err?.response?.data?.error || err?.response?.data?.detail || 'Backup failed');
    } finally {
      setBackupLoading(false);
    }
  };

  const handleRestore = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.db')) {
      setBackupError('Please select a .db file');
      return;
    }
    setRestoreLoading(true);
    setBackupMsg('');
    setBackupError('');
    try {
      const form = new FormData();
      form.append('file', file);
      await apiClient.post('/company/backup', form);
      setBackupMsg('Database restored successfully. Please restart the server.');
    } catch (err: any) {
      setBackupError(err?.response?.data?.error || err?.response?.data?.detail || 'Restore failed');
    } finally {
      setRestoreLoading(false);
      e.target.value = ''; // reset file input
    }
  };

  const handleResetDatabase = async () => {
    setResetLoading(true);
    setResetMsg('');
    setResetError('');
    try {
      const resp = await apiClient.post('/company/reset', {
        keep_users: resetKeepUsers,
        keep_branches: resetKeepBranches,
        keep_company: resetKeepCompany,
        keep_products: resetKeepProducts,
        keep_customers: resetKeepCustomers,
      });
      setResetMsg(resp.data?.message || 'Database reset completed.');
      setResetConfirm(false);
    } catch (err: any) {
      setResetError(err?.response?.data?.error || err?.response?.data?.detail || 'Reset failed');
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <Box>
      <PageHeader title="Settings" subtitle="Manage your account and system preferences" />

      <Grid container spacing={3}>
        {/* Profile Info */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Avatar sx={{ width: 56, height: 56, bgcolor: 'primary.main', fontSize: 22 }}>
                  {user?.full_name?.charAt(0)?.toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || 'U'}
                </Avatar>
                <Box>
                  <Typography variant="h6" sx={{ lineHeight: 1.2 }}>
                    {user?.full_name || user?.username || 'User'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">{user?.email || '—'}</Typography>
                </Box>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><PersonIcon fontSize="small" color="action" /></ListItemIcon>
                  <ListItemText primary="Username" secondary={user?.username || '—'} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}><LockIcon fontSize="small" color="action" /></ListItemIcon>
                  <ListItemText
                    primary="Role"
                    secondary={
                      <Chip label={user?.role_name || 'Unknown'} size="small" color="primary" variant="outlined" sx={{ mt: 0.5 }} />
                    }
                    secondaryTypographyProps={{ component: 'div' } as any}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Change Password */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <LockIcon color="primary" />
                <Typography variant="h6">Change Password</Typography>
              </Box>
              <Divider sx={{ mb: 3 }} />
              <Box component="form" onSubmit={handlePasswordChange}>
                <Grid container spacing={2}>
                  <Grid size={12}>
                    <TextField
                      label="Current Password"
                      type="password"
                      value={oldPassword}
                      onChange={(e) => setOldPassword(e.target.value)}
                      required fullWidth
                      autoComplete="current-password"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      label="New Password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required fullWidth
                      autoComplete="new-password"
                      helperText="At least 6 characters"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      label="Confirm New Password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required fullWidth
                      autoComplete="new-password"
                      error={!!confirmPassword && confirmPassword !== newPassword}
                      helperText={confirmPassword && confirmPassword !== newPassword ? 'Passwords do not match' : ''}
                    />
                  </Grid>
                  {pwdError && (
                    <Grid size={12}>
                      <Alert severity="error">{pwdError}</Alert>
                    </Grid>
                  )}
                  <Grid size={12}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={pwdLoading || !oldPassword || !newPassword || !confirmPassword}
                      startIcon={pwdLoading ? <CircularProgress size={16} color="inherit" /> : <LockIcon />}
                    >
                      {pwdLoading ? 'Updating...' : 'Update Password'}
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Preferences */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <PaletteIcon color="primary" />
                <Typography variant="h6">Display Preferences</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <FormControlLabel
                control={
                  <Switch
                    checked={denseMode}
                    onChange={handleDenseModeToggle}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight={500}>Dense Mode</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Compact table rows and reduced spacing
                    </Typography>
                  </Box>
                }
                sx={{ alignItems: 'flex-start', ml: 0 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* API Health */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <StorageIcon color="primary" />
                <Typography variant="h6">API Connectivity</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleCheckApi}
                  disabled={apiStatus === 'checking'}
                  startIcon={apiStatus === 'checking' ? <CircularProgress size={14} /> : <CheckCircleIcon />}
                >
                  {apiStatus === 'checking' ? 'Checking...' : 'Test Connection'}
                </Button>
                {apiStatus === 'ok' && (
                  <Chip
                    label={`Connected · ${apiLatency}ms`}
                    color="success"
                    size="small"
                    icon={<CheckCircleIcon />}
                  />
                )}
                {apiStatus === 'error' && (
                  <Chip label="Connection Failed" color="error" size="small" />
                )}
              </Box>
              <Typography variant="caption" color="text.secondary">
                Backend URL: <strong>http://localhost:5000/api/v1</strong>
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Company Info */}
        <Grid size={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <BusinessIcon color="primary" />
                <Typography variant="h6">Company Information</Typography>
              </Box>
              <Divider sx={{ mb: 3 }} />
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField label="Company Name" value={companyForm.name || ''} onChange={(e) => setCompanyForm(f => ({ ...f, name: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField label="Legal Name" value={companyForm.legal_name || ''} onChange={(e) => setCompanyForm(f => ({ ...f, legal_name: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <TextField label="Tax ID / TIN" value={companyForm.tax_id || ''} onChange={(e) => setCompanyForm(f => ({ ...f, tax_id: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <TextField label="Phone" value={companyForm.phone || ''} onChange={(e) => setCompanyForm(f => ({ ...f, phone: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <TextField label="Email" value={companyForm.email || ''} onChange={(e) => setCompanyForm(f => ({ ...f, email: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField label="Website" value={companyForm.website || ''} onChange={(e) => setCompanyForm(f => ({ ...f, website: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={{ xs: 12, sm: 3 }}>
                  <TextField label="Currency" value={companyForm.currency || 'ETB'} onChange={(e) => setCompanyForm(f => ({ ...f, currency: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={{ xs: 12, sm: 3 }}>
                  <TextField label="Fiscal Year Start (MM-DD)" value={companyForm.fiscal_year_start || '07-01'} onChange={(e) => setCompanyForm(f => ({ ...f, fiscal_year_start: e.target.value }))} fullWidth disabled={!isOwner} />
                </Grid>
                <Grid size={12}>
                  <TextField label="Address" value={companyForm.address || ''} onChange={(e) => setCompanyForm(f => ({ ...f, address: e.target.value }))} fullWidth multiline rows={2} disabled={!isOwner} />
                </Grid>
                {isOwner && (
                  <Grid size={12}>
                    <Button variant="contained" onClick={handleCompanyUpdate} disabled={companyLoading} startIcon={companyLoading ? <CircularProgress size={16} color="inherit" /> : <BusinessIcon />}>
                      {companyLoading ? 'Saving...' : 'Save Company Info'}
                    </Button>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Backup & Restore */}
        {isOwner && (
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <StorageIcon color="primary" />
                  <Typography variant="h6">Backup & Restore</Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                {backupMsg && (
                  <Alert severity="success" sx={{ mb: 2 }} onClose={() => setBackupMsg('')}>{backupMsg}</Alert>
                )}
                {backupError && (
                  <Alert severity="error" sx={{ mb: 2 }} onClose={() => setBackupError('')}>{backupError}</Alert>
                )}
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    startIcon={backupLoading ? <CircularProgress size={16} color="inherit" /> : <CloudDownloadIcon />}
                    onClick={handleBackup}
                    disabled={backupLoading || restoreLoading}
                  >
                    {backupLoading ? 'Creating Backup...' : 'Download Backup'}
                  </Button>
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<CloudUploadIcon />}
                    disabled={backupLoading || restoreLoading}
                  >
                    {restoreLoading ? 'Restoring...' : 'Restore from Backup'}
                    <input type="file" hidden accept=".db" onChange={handleRestore} />
                  </Button>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: 'block' }}>
                  Backup creates a snapshot of the SQLite database. Restore replaces the current database with the uploaded file — use with caution.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Reset Database */}
        {isOwner && (
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <DeleteSweepIcon color="error" />
                  <Typography variant="h6" color="error">Reset Database</Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                {resetMsg && (
                  <Alert severity="success" sx={{ mb: 2 }} onClose={() => setResetMsg('')}>{resetMsg}</Alert>
                )}
                {resetError && (
                  <Alert severity="error" sx={{ mb: 2 }} onClose={() => setResetError('')}>{resetError}</Alert>
                )}
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Select which data to preserve. Unchecked items will be deleted.
                </Typography>
                <Grid container spacing={1} sx={{ mb: 2 }}>
                  <Grid size={12}>
                    <FormControlLabel
                      control={<Switch checked={resetKeepUsers} onChange={(e) => setResetKeepUsers(e.target.checked)} color="primary" />}
                      label={<><Typography variant="body2" fontWeight={500}>Keep Users</Typography><Typography variant="caption" color="text.secondary" display="block">Users, roles, permissions</Typography></>}
                      sx={{ alignItems: 'flex-start', ml: 0 }}
                    />
                  </Grid>
                  <Grid size={12}>
                    <FormControlLabel
                      control={<Switch checked={resetKeepBranches} onChange={(e) => setResetKeepBranches(e.target.checked)} color="primary" />}
                      label={<><Typography variant="body2" fontWeight={500}>Keep Branches</Typography><Typography variant="caption" color="text.secondary" display="block">Branches and warehouses</Typography></>}
                      sx={{ alignItems: 'flex-start', ml: 0 }}
                    />
                  </Grid>
                  <Grid size={12}>
                    <FormControlLabel
                      control={<Switch checked={resetKeepCompany} onChange={(e) => setResetKeepCompany(e.target.checked)} color="primary" />}
                      label={<><Typography variant="body2" fontWeight={500}>Keep Company</Typography><Typography variant="caption" color="text.secondary" display="block">Company information</Typography></>}
                      sx={{ alignItems: 'flex-start', ml: 0 }}
                    />
                  </Grid>
                  <Grid size={12}>
                    <FormControlLabel
                      control={<Switch checked={resetKeepProducts} onChange={(e) => setResetKeepProducts(e.target.checked)} color="primary" />}
                      label={<><Typography variant="body2" fontWeight={500}>Keep Products</Typography><Typography variant="caption" color="text.secondary" display="block">Products, categories, units, inventory</Typography></>}
                      sx={{ alignItems: 'flex-start', ml: 0 }}
                    />
                  </Grid>
                  <Grid size={12}>
                    <FormControlLabel
                      control={<Switch checked={resetKeepCustomers} onChange={(e) => setResetKeepCustomers(e.target.checked)} color="primary" />}
                      label={<><Typography variant="body2" fontWeight={500}>Keep Customers</Typography><Typography variant="caption" color="text.secondary" display="block">Customers and their history</Typography></>}
                      sx={{ alignItems: 'flex-start', ml: 0 }}
                    />
                  </Grid>
                </Grid>
                {!resetConfirm ? (
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteSweepIcon />}
                    onClick={() => setResetConfirm(true)}
                    disabled={resetLoading}
                  >
                    Reset Database
                  </Button>
                ) : (
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Button
                      variant="contained"
                      color="error"
                      startIcon={resetLoading ? <CircularProgress size={16} color="inherit" /> : <DeleteSweepIcon />}
                      onClick={handleResetDatabase}
                      disabled={resetLoading}
                    >
                      {resetLoading ? 'Resetting...' : 'Confirm Reset'}
                    </Button>
                    <Button variant="text" onClick={() => setResetConfirm(false)} disabled={resetLoading}>
                      Cancel
                    </Button>
                    <Typography variant="caption" color="text.secondary">
                      This action cannot be undone.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* System Info */}
        <Grid size={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <InfoIcon color="primary" />
                <Typography variant="h6">System Information</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                {[
                  { label: 'Application', value: 'ETA Factory' },
                  { label: 'Version', value: 'v1.0.0' },
                  { label: 'Environment', value: 'Development' },
                  { label: 'Frontend', value: 'React 18 + Vite + MUI v6' },
                  { label: 'Backend', value: 'Python / Flask + SQLAlchemy' },
                  { label: 'Database', value: 'SQLite (dev) / PostgreSQL (prod)' },
                ].map(({ label, value }) => (
                  <Grid size={{ xs: 12, sm: 6, md: 4 }} key={label}>
                    <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
                      <Typography variant="caption" color="text.secondary">{label}</Typography>
                      <Typography variant="body2" fontWeight={500}>{value}</Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar open={pwdSuccess} autoHideDuration={4000} onClose={() => setPwdSuccess(false)}>
        <Alert severity="success" onClose={() => setPwdSuccess(false)}>
          Password updated successfully!
        </Alert>
      </Snackbar>
      <Snackbar open={companySuccess} autoHideDuration={4000} onClose={() => setCompanySuccess(false)}>
        <Alert severity="success" onClose={() => setCompanySuccess(false)}>
          Company information updated successfully!
        </Alert>
      </Snackbar>
      <Snackbar open={!!companyError} autoHideDuration={6000} onClose={() => setCompanyError('')}>
        <Alert severity="error" onClose={() => setCompanyError('')}>{companyError}</Alert>
      </Snackbar>
    </Box>
  );
}
