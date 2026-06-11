import { Box, Typography, Button, Breadcrumbs, Link } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import HomeIcon from '@mui/icons-material/Home';
import { useNavigate, useLocation, Link as RouterLink } from 'react-router-dom';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: { label: string; path?: string; icon?: React.ReactNode };
  onActionClick?: () => void;
  hideBreadcrumbs?: boolean;
}

export default function PageHeader({ title, subtitle, action, onActionClick, hideBreadcrumbs }: PageHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const generateBreadcrumbs = () => {
    const pathnames = location.pathname.split('/').filter((x) => x);
    if (pathnames.length === 0) return null;

    return (
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb" sx={{ mb: 1 }}>
        <Link component={RouterLink} to="/dashboard" color="inherit" sx={{ display: 'flex', alignItems: 'center' }}>
          <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
        </Link>
        {pathnames.map((value, index) => {
          const last = index === pathnames.length - 1;
          const to = `/${pathnames.slice(0, index + 1).join('/')}`;
          const label = value.charAt(0).toUpperCase() + value.slice(1).replace(/-/g, ' ');

          return last ? (
            <Typography color="text.primary" key={to} sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
              {label}
            </Typography>
          ) : (
            <Link component={RouterLink} to={to} color="inherit" key={to} sx={{ fontSize: '0.875rem', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
              {label}
            </Link>
          );
        })}
      </Breadcrumbs>
    );
  };

  return (
    <Box sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
      <Box>
        {!hideBreadcrumbs && generateBreadcrumbs()}
        <Typography variant="h4" sx={{ fontWeight: 700, color: 'text.primary', letterSpacing: '-0.5px' }}>{title}</Typography>
        {subtitle && <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{subtitle}</Typography>}
      </Box>
      {action && (
        <Button variant="contained" color="primary" startIcon={action.icon || <AddIcon />} onClick={() => { if (onActionClick) onActionClick(); else if (action.path) navigate(action.path); }} sx={{ borderRadius: 1.5, px: 2, py: 0.75 }}>
          {action.label}
        </Button>
      )}
    </Box>
  );
}
