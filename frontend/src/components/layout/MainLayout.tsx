import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, AppBar, Toolbar, Typography, IconButton, List, ListItem, ListItemButton,
  ListItemIcon, ListItemText, Avatar, Menu, MenuItem, Divider, useMediaQuery, useTheme,
  Collapse, Tooltip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import DashboardIcon from '@mui/icons-material/Dashboard';
import InventoryIcon from '@mui/icons-material/Inventory';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import PeopleIcon from '@mui/icons-material/People';
import StoreIcon from '@mui/icons-material/Store';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import AssessmentIcon from '@mui/icons-material/Assessment';
import SettingsIcon from '@mui/icons-material/Settings';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import GroupIcon from '@mui/icons-material/Group';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing';
import ReceiptIcon from '@mui/icons-material/Receipt';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import SecurityIcon from '@mui/icons-material/Security';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import DeleteIcon from '@mui/icons-material/Delete';
import { useAuthStore } from '../../store/authStore';
import { useCompanyStore } from '../../store/companyStore';
import { authApi } from '../../api/endpoints';

const DRAWER_WIDTH = 280;
const COLLAPSED_DRAWER_WIDTH = 72;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  roles?: string[];
  children?: NavItem[];
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

const navigation: NavGroup[] = [
  {
    group: 'Operations',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
      { label: 'Reports', path: '/reports', icon: <AssessmentIcon /> },
      { label: 'Audit Logs', path: '/audit', icon: <SecurityIcon />, roles: ['Owner', 'Auditor', 'General Manager'] },
    ]
  },
  {
    group: 'Sales',
    items: [
      { label: 'Customers', path: '/customers', icon: <PeopleIcon /> },
      { label: 'Sales Quotations', path: '/sales/quotations', icon: <ReceiptIcon /> },
      { label: 'Sales Orders', path: '/sales/orders', icon: <ShoppingCartIcon /> },
      { label: 'Invoices', path: '/sales/invoices', icon: <ReceiptLongIcon /> },
      { label: 'Payments', path: '/sales/payments', icon: <FactCheckIcon /> },
    ]
  },
  {
    group: 'Inventory',
    items: [
      { label: 'Dashboard', path: '/inventory/dashboard', icon: <AssessmentIcon /> },
      {
        label: 'Products', path: '/products', icon: <InventoryIcon />,
        children: [
          { label: 'Products', path: '/products', icon: <InventoryIcon /> },
          { label: 'Categories', path: '/settings/categories', icon: <InventoryIcon /> },
          { label: 'Units', path: '/settings/units', icon: <InventoryIcon /> },
        ]
      },
      { label: 'Stock Levels', path: '/inventory', icon: <InventoryIcon /> },
      { label: 'Low Stock Alerts', path: '/inventory/low-stock', icon: <WarningAmberIcon /> },
      { label: 'Inventory Ledger', path: '/inventory/ledger', icon: <FactCheckIcon /> },
      { label: 'Bin Card', path: '/inventory/bin-card', icon: <ReceiptIcon /> },
      { label: 'Opening Balances', path: '/inventory/opening-balances', icon: <WarehouseIcon /> },
      { label: 'Transfers', path: '/transfers', icon: <AccountTreeIcon /> },
      {
        label: 'Warehouses', path: '/warehouses', icon: <WarehouseIcon />,
        children: [
          { label: 'GRV', path: '/warehouses/grv', icon: <StoreIcon /> },
          { label: 'GIV', path: '/warehouses/giv', icon: <LocalShippingIcon /> },
          { label: 'Disposal', path: '/warehouses/disposal', icon: <DeleteIcon /> },
          { label: 'Adjustments', path: '/warehouses/adjustments', icon: <InventoryIcon /> },
          { label: 'Stocktake', path: '/warehouses/stocktake', icon: <FactCheckIcon /> },
        ]
      },
    ]
  },
  {
    group: 'Manufacturing',
    items: [
      { label: 'Production', path: '/production/batches', icon: <PrecisionManufacturingIcon /> },
    ]
  },
  {
    group: 'Administration',
    items: [
      { label: 'Users', path: '/users', icon: <GroupIcon />, roles: ['Owner', 'General Manager'] },
      { label: 'Branches', path: '/branches', icon: <AccountTreeIcon />, roles: ['Owner', 'General Manager'] },
      { label: 'Settings', path: '/settings', icon: <SettingsIcon />, roles: ['Owner'] },
    ]
  }
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, logout, hasRole, setUser } = useAuthStore();
  const { company, fetchCompany } = useCompanyStore();

  useEffect(() => {
    fetchCompany();
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && !user) {
      authApi.me().then(setUser).catch(() => logout());
    }
  }, [user, logout, setUser]);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  // Initialize open groups and items based on the current path
  const getInitialState = () => {
    const initialGroups: Record<string, boolean> = {};
    const initialItems: Record<string, boolean> = {};
    let activeGroup: string | null = null;
    
    navigation.forEach(group => {
      group.items.forEach(item => {
        if (item.children) {
          const childActive = item.children.some(c => location.pathname.startsWith(c.path));
          if (childActive) {
            initialItems[item.path] = true;
            activeGroup = group.group;
          }
        } else if (location.pathname.startsWith(item.path)) {
          activeGroup = group.group;
        }
      });
    });
    
    if (activeGroup) initialGroups[activeGroup] = true;
    return { initialGroups, initialItems };
  };

  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(getInitialState().initialGroups);
  const [openItems, setOpenItems] = useState<Record<string, boolean>>(getInitialState().initialItems);

  useEffect(() => {
    let activeGroup: string | null = null;
    const activeItems: Record<string, boolean> = {};

    navigation.forEach(group => {
      group.items.forEach(item => {
        if (item.children && item.children.some(c => location.pathname.startsWith(c.path))) {
          activeItems[item.path] = true;
          activeGroup = group.group;
        } else if (!item.children && location.pathname.startsWith(item.path)) {
          activeGroup = group.group;
        }
      });
    });

    if (activeGroup) setOpenGroups({ [activeGroup]: true });
    if (Object.keys(activeItems).length) setOpenItems(prev => ({ ...prev, ...activeItems }));
  }, [location.pathname]);

  const handleDrawerToggle = () => {
    if (isMobile) {
      setMobileOpen(!mobileOpen);
    } else {
      setCollapsed(!collapsed);
    }
  };

  const toggleGroup = (group: string) => {
    setOpenGroups((prev) => {
      const isOpening = !prev[group];
      const next: Record<string, boolean> = {};
      if (isOpening) next[group] = true;
      return next;
    });
  };

  const toggleItem = (path: string) => {
    setOpenItems((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const drawerWidth = isMobile ? DRAWER_WIDTH : (collapsed ? COLLAPSED_DRAWER_WIDTH : DRAWER_WIDTH);

  // Resolve active item in a group: prefer the most specific (longest) path match
  const resolveActive = (items: NavItem[]): string | null => {
    let best: string | null = null;
    for (const item of items) {
      if (item.children) {
        for (const child of item.children) {
          if (location.pathname.startsWith(child.path)) {
            if (!best || child.path.length > best.length) best = child.path;
          }
        }
      } else if (location.pathname.startsWith(item.path)) {
        if (!best || item.path.length > best.length) best = item.path;
      }
    }
    return best;
  };

  // Helper to render individual navigation items (supports 1 level of nesting)
  const renderNavItem = (item: NavItem, depth = 0, groupItems?: NavItem[]) => {
    const hasChildren = !!item.children;
    const isItemOpen = openItems[item.path] === true;
    
    const active = hasChildren 
      ? item.children!.some(c => location.pathname.startsWith(c.path))
      : (groupItems ? resolveActive(groupItems) === item.path : location.pathname.startsWith(item.path));

    const listItemButton = (
      <ListItemButton
        selected={!hasChildren && active}
        onClick={() => {
          navigate(item.path);
          if (hasChildren) {
            toggleItem(item.path);
            if (collapsed && !isMobile) setCollapsed(false);
          }
          if (isMobile) setMobileOpen(false);
        }}
        sx={{
          borderRadius: 1.5,
          mb: 0.5,
          justifyContent: collapsed && !isMobile && depth === 0 ? 'center' : 'flex-start',
          px: collapsed && !isMobile && depth === 0 ? 1 : (1.5 + depth * 1.5),
          py: 1,
          '&.Mui-selected': {
            bgcolor: 'primary.light',
            color: 'primary.contrastText',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            '&:hover': { bgcolor: 'primary.main' },
            '& .MuiListItemIcon-root': { color: 'inherit' }
          },
          '&:hover': {
            bgcolor: (!hasChildren && active) ? 'primary.main' : 'rgba(0,0,0,0.04)',
          }
        }}
      >
        <ListItemIcon sx={{ minWidth: collapsed && !isMobile && depth === 0 ? 0 : 36, color: (!hasChildren && active) ? 'inherit' : 'text.secondary', justifyContent: 'center' }}>
          {item.icon}
        </ListItemIcon>
        {(!collapsed || isMobile || depth > 0) && (
          <ListItemText 
            primary={item.label} 
            primaryTypographyProps={{ fontSize: depth > 0 ? '0.8125rem' : '0.875rem', fontWeight: active ? 600 : 500 }} 
          />
        )}
        {hasChildren && (!collapsed || isMobile) && (
          isItemOpen ? <ExpandLess sx={{ fontSize: 18, color: 'text.secondary' }} /> : <ExpandMore sx={{ fontSize: 18, color: 'text.secondary' }} />
        )}
      </ListItemButton>
    );

    const renderedItem = (
      <ListItem key={item.path} disablePadding sx={{ display: 'block' }}>
        {collapsed && !isMobile && depth === 0 ? (
          <Tooltip title={item.label} placement="right" arrow>
            {listItemButton}
          </Tooltip>
        ) : (
          listItemButton
        )}
      </ListItem>
    );

    if (hasChildren) {
      return (
        <Box key={item.path}>
          {renderedItem}
          <Collapse in={isItemOpen && (!collapsed || isMobile)} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.filter(c => !c.roles || c.roles.some(r => hasRole(r))).map(child => renderNavItem(child, depth + 1))}
            </List>
          </Collapse>
        </Box>
      );
    }

    return renderedItem;
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Box sx={{ py: 2, px: collapsed && !isMobile ? 1 : 2.5, display: 'flex', alignItems: 'center', gap: 1, minHeight: 64 }}>
        <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36, fontSize: 14, fontWeight: 700, mx: collapsed && !isMobile ? 'auto' : 0 }}>
          {company?.name?.charAt(0) || 'E'}
        </Avatar>
        {(!collapsed || isMobile) && (
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {company?.name || 'ETA Factory'}
            </Typography>
          </Box>
        )}
      </Box>
      <Divider />
      <List sx={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', px: 1.5, py: 1, '&::-webkit-scrollbar': { width: '6px' }, '&::-webkit-scrollbar-thumb': { backgroundColor: 'rgba(0,0,0,.1)', borderRadius: '4px' } }}>
        {navigation.map((navGroup) => {
          const visibleItems = navGroup.items.filter(
            (item) => !item.roles || item.roles.some((r) => hasRole(r))
          );
          
          if (visibleItems.length === 0) return null;

          const isGroupOpen = openGroups[navGroup.group] === true;

          return (
            <Box key={navGroup.group} sx={{ mb: 1 }}>
              {(!collapsed || isMobile) && (
                <ListItemButton 
                  onClick={() => toggleGroup(navGroup.group)}
                  sx={{ 
                    borderRadius: 1, 
                    py: 0.5, 
                    mb: 0.5,
                    '&:hover': { bgcolor: 'rgba(0,0,0,0.04)' }
                  }}
                >
                  <ListItemText 
                    primary={navGroup.group} 
                    primaryTypographyProps={{ 
                      fontSize: '0.75rem', 
                      fontWeight: 700, 
                      color: 'text.secondary', 
                      textTransform: 'uppercase', 
                      letterSpacing: '0.5px' 
                    }} 
                  />
                  {isGroupOpen ? <ExpandLess sx={{ color: 'text.secondary', fontSize: 20 }} /> : <ExpandMore sx={{ color: 'text.secondary', fontSize: 20 }} />}
                </ListItemButton>
              )}
              
              {collapsed && !isMobile && <Divider sx={{ my: 1 }} />}
              
              <Collapse in={isGroupOpen || (collapsed && !isMobile)} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {visibleItems.map((item) => renderNavItem(item, 0, visibleItems))}
                </List>
              </Collapse>
            </Box>
          );
        })}
      </List>
      {(!collapsed || isMobile) && (
        <Box sx={{ px: 2.5, py: 1.5, borderTop: '1px solid', borderColor: 'divider' }}>
          <Typography variant="caption" color="text.secondary">
            powered by ETA Factory
          </Typography>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      {isMobile ? (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          sx={{ '& .MuiDrawer-paper': { width: drawerWidth, border: 'none', boxShadow: '4px 0 24px rgba(0,0,0,0.08)' } }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        <Drawer
          variant="permanent"
          sx={{ 
            width: drawerWidth, 
            flexShrink: 0, 
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            '& .MuiDrawer-paper': { 
              width: drawerWidth, 
              borderRight: '1px solid', 
              borderColor: 'divider',
              overflowX: 'hidden',
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            } 
          }}
        >
          {drawerContent}
        </Drawer>
      )}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <AppBar position="sticky" color="inherit" elevation={0} sx={{ borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
          <Toolbar sx={{ minHeight: '64px !important' }}>
            <IconButton edge="start" onClick={handleDrawerToggle} sx={{ mr: 2, color: 'text.secondary' }}>
              <MenuIcon />
            </IconButton>
            <Box sx={{ flex: 1 }}>
              {/* Breadcrumbs can be injected here dynamically or by the PageHeader */}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                  {user?.full_name}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  {user?.role_name}
                </Typography>
              </Box>
              <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small">
                <Avatar sx={{ width: 36, height: 36, bgcolor: 'primary.main', fontSize: 14, fontWeight: 600 }}>
                  {user?.full_name?.charAt(0)}
                </Avatar>
              </IconButton>
              <Menu 
                anchorEl={anchorEl} 
                open={Boolean(anchorEl)} 
                onClose={() => setAnchorEl(null)}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                PaperProps={{ sx: { width: 200, mt: 1, boxShadow: '0 4px 20px rgba(0,0,0,0.1)' } }}
              >
                <Box sx={{ px: 2, py: 1.5, display: { xs: 'block', sm: 'none' } }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{user?.full_name}</Typography>
                  <Typography variant="caption" color="text.secondary">{user?.role_name}</Typography>
                </Box>
                <Divider sx={{ display: { xs: 'block', sm: 'none' } }} />
                <MenuItem onClick={() => { setAnchorEl(null); navigate('/settings'); }} sx={{ py: 1.5 }}>
                  <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
                  Settings
                </MenuItem>
                <MenuItem onClick={() => { setAnchorEl(null); logout(); navigate('/login'); }} sx={{ py: 1.5, color: 'error.main' }}>
                  <ListItemIcon><SecurityIcon fontSize="small" sx={{ color: 'error.main' }} /></ListItemIcon>
                  Logout
                </MenuItem>
              </Menu>
            </Box>
          </Toolbar>
        </AppBar>
        <Box sx={{ flex: 1, p: { xs: 2, sm: 3, md: 4 }, overflow: 'auto', bgcolor: 'background.default' }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
