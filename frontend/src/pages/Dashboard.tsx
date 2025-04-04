import React from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box, 
  Card, 
  CardContent, 
  Divider, 
  useTheme,
  CircularProgress,
  Tooltip,
  IconButton,
  useMediaQuery
} from '@mui/material';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useQuery } from 'react-query';
import axios from 'axios';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import InfoIcon from '@mui/icons-material/Info';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import SecurityIcon from '@mui/icons-material/Security';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import DiamondIcon from '@mui/icons-material/Diamond';
import StarIcon from '@mui/icons-material/Star';

interface PortfolioSummary {
  total_value: number;
  asset_allocation: Record<string, number>;
  risk_metrics: {
    beta: number;
    sharpe_ratio: number;
    volatility: number;
  };
}

const Dashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const { data: portfolioSummary, isLoading } = useQuery<PortfolioSummary>(
    'portfolioSummary',
    async () => {
      const response = await axios.get('http://localhost:8000/api/v1/portfolios/summary');
      return response.data;
    }
  );

  if (isLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '80vh',
        background: 'url("https://images.unsplash.com/photo-1579546929518-9e396f3cc809?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 1
        }
      }}>
        <CircularProgress size={60} sx={{ color: '#D4AF37', zIndex: 2 }} />
      </Box>
    );
  }

  const assetAllocationData = portfolioSummary
    ? Object.entries(portfolioSummary.asset_allocation).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  // Renaissance-inspired colors
  const COLORS = ['#D4AF37', '#8B4513', '#800020', '#2F4F4F', '#4B0082', '#8B0000'];

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  // Get risk level based on metrics
  const getRiskLevel = () => {
    if (!portfolioSummary) return 'Low';
    
    const { beta, volatility } = portfolioSummary.risk_metrics;
    
    if (beta < 0.8 && volatility < 10) return 'Low';
    if (beta < 1.2 && volatility < 15) return 'Moderate';
    if (beta < 1.5 && volatility < 20) return 'Moderate-High';
    return 'High';
  };

  // Get risk level color
  const getRiskLevelColor = () => {
    const riskLevel = getRiskLevel();
    switch (riskLevel) {
      case 'Low': return '#D4AF37'; // Gold
      case 'Moderate': return '#8B4513'; // Sienna
      case 'Moderate-High': return '#800020'; // Burgundy
      case 'High': return '#8B0000'; // Dark Red
      default: return '#D4AF37';
    }
  };

  // Renaissance card style
  const renaissanceCardStyle = (gradientStart: string, gradientEnd: string) => ({
    height: '100%',
    borderRadius: 2,
    background: `linear-gradient(135deg, ${gradientStart} 0%, ${gradientEnd} 100%)`,
    color: '#F5F5DC', // Cream color
    transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
    position: 'relative',
    overflow: 'hidden',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'url("https://www.transparenttextures.com/patterns/diamond-upholstery.png")',
      opacity: 0.1,
      zIndex: 0
    },
    '&::after': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '5px',
      background: '#D4AF37', // Gold border
      zIndex: 1
    },
    '&:hover': {
      transform: 'translateY(-5px)',
      boxShadow: '0 12px 20px rgba(0, 0, 0, 0.3)'
    }
  });

  // Renaissance divider style
  const renaissanceDividerStyle = {
    height: '2px',
    background: 'linear-gradient(90deg, transparent, #D4AF37, transparent)',
    margin: '16px 0',
    opacity: 0.7
  };

  // Renaissance title style
  const renaissanceTitleStyle = {
    fontFamily: 'serif',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    textShadow: '2px 2px 4px rgba(0, 0, 0, 0.3)',
    position: 'relative',
    display: 'inline-block',
    '&::after': {
      content: '""',
      position: 'absolute',
      bottom: '-8px',
      left: '0',
      width: '100%',
      height: '2px',
      background: 'linear-gradient(90deg, transparent, #D4AF37, transparent)'
    }
  };

  return (
    <Box sx={{ 
      p: 3, 
      maxWidth: 1400, 
      mx: 'auto',
      background: 'url("https://images.unsplash.com/photo-1579546929518-9e396f3cc809?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80")',
      backgroundSize: 'cover',
      backgroundAttachment: 'fixed',
      minHeight: '100vh',
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        zIndex: 0
      }
    }}>
      <Box sx={{ position: 'relative', zIndex: 1 }}>
        <Typography 
          variant="h3" 
          gutterBottom 
          align="center"
          sx={{ 
            mb: 4,
            fontWeight: 'bold',
            color: '#D4AF37',
            fontFamily: 'serif',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            textShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)',
            position: 'relative',
            '&::before, &::after': {
              content: '""',
              position: 'absolute',
              top: '50%',
              width: '100px',
              height: '2px',
              background: '#D4AF37',
              opacity: 0.7
            },
            '&::before': {
              left: 'calc(50% - 150px)'
            },
            '&::after': {
              right: 'calc(50% - 150px)'
            }
          }}
        >
          Portfolio Dashboard
        </Typography>
        
        <Grid container spacing={3}>
          {/* Total Value Card */}
          <Grid item xs={12} md={4}>
            <Card 
              elevation={3} 
              sx={renaissanceCardStyle('#2F4F4F', '#1a2f2f')}
            >
              <CardContent sx={{ p: 3, position: 'relative', zIndex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AccountBalanceIcon sx={{ fontSize: 40, mr: 1, color: '#D4AF37' }} />
                  <Typography variant="h6" component="div" sx={renaissanceTitleStyle}>
                    Total Portfolio Value
                  </Typography>
                </Box>
                <Divider sx={renaissanceDividerStyle} />
                <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', color: '#D4AF37', textShadow: '1px 1px 2px rgba(0, 0, 0, 0.5)' }}>
                  {portfolioSummary ? formatCurrency(portfolioSummary.total_value) : '$0'}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <TrendingUpIcon sx={{ mr: 1, color: '#D4AF37' }} />
                  <Typography variant="body2">
                    {portfolioSummary && portfolioSummary.total_value > 0 ? 'Active Portfolio' : 'No Assets'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Risk Level Card */}
          <Grid item xs={12} md={4}>
            <Card 
              elevation={3} 
              sx={renaissanceCardStyle('#800020', '#4a0012')}
            >
              <CardContent sx={{ p: 3, position: 'relative', zIndex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <SecurityIcon sx={{ fontSize: 40, mr: 1, color: '#D4AF37' }} />
                  <Typography variant="h6" component="div" sx={renaissanceTitleStyle}>
                    Risk Profile
                  </Typography>
                </Box>
                <Divider sx={renaissanceDividerStyle} />
                <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', color: getRiskLevelColor(), textShadow: '1px 1px 2px rgba(0, 0, 0, 0.5)' }}>
                  {getRiskLevel()}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <Typography variant="body2">
                    Based on beta and volatility metrics
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Asset Count Card */}
          <Grid item xs={12} md={4}>
            <Card 
              elevation={3} 
              sx={renaissanceCardStyle('#8B4513', '#5c2e0c')}
            >
              <CardContent sx={{ p: 3, position: 'relative', zIndex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <DiamondIcon sx={{ fontSize: 40, mr: 1, color: '#D4AF37' }} />
                  <Typography variant="h6" component="div" sx={renaissanceTitleStyle}>
                    Asset Diversification
                  </Typography>
                </Box>
                <Divider sx={renaissanceDividerStyle} />
                <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', color: '#D4AF37', textShadow: '1px 1px 2px rgba(0, 0, 0, 0.5)' }}>
                  {assetAllocationData.length}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <Typography variant="body2">
                    {assetAllocationData.length > 0 ? 'Different asset types' : 'No assets added yet'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Risk Metrics Card */}
          <Grid item xs={12} md={6}>
            <Card 
              elevation={3} 
              sx={{ 
                borderRadius: 2,
                height: '100%',
                background: 'rgba(0, 0, 0, 0.7)',
                border: '1px solid #D4AF37',
                transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-5px)',
                  boxShadow: '0 12px 20px rgba(0, 0, 0, 0.3)'
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h5" component="div" sx={{ ...renaissanceTitleStyle, color: '#D4AF37' }}>
                    Risk Metrics
                  </Typography>
                  <Tooltip title="Risk metrics help you understand the volatility and market sensitivity of your portfolio">
                    <IconButton size="small" sx={{ ml: 1, color: '#D4AF37' }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Divider sx={renaissanceDividerStyle} />
                <Grid container spacing={3}>
                  <Grid item xs={4}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      borderRadius: 2, 
                      bgcolor: 'rgba(0, 0, 0, 0.5)',
                      border: '1px solid #D4AF37',
                      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)'
                    }}>
                      <Typography variant="subtitle2" sx={{ color: '#D4AF37' }}>Beta</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 'bold', mt: 1, color: '#F5F5DC' }}>
                        {portfolioSummary?.risk_metrics?.beta?.toFixed(2) || '0.00'}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#D4AF37' }}>
                        {portfolioSummary?.risk_metrics?.beta && portfolioSummary.risk_metrics.beta > 1 ? 'Higher than market' : 'Lower than market'}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      borderRadius: 2, 
                      bgcolor: 'rgba(0, 0, 0, 0.5)',
                      border: '1px solid #D4AF37',
                      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)'
                    }}>
                      <Typography variant="subtitle2" sx={{ color: '#D4AF37' }}>Sharpe Ratio</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 'bold', mt: 1, color: '#F5F5DC' }}>
                        {portfolioSummary?.risk_metrics?.sharpe_ratio?.toFixed(2) || '0.00'}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#D4AF37' }}>
                        {portfolioSummary?.risk_metrics?.sharpe_ratio && portfolioSummary.risk_metrics.sharpe_ratio > 1 ? 'Good risk-adjusted return' : 'Poor risk-adjusted return'}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      borderRadius: 2, 
                      bgcolor: 'rgba(0, 0, 0, 0.5)',
                      border: '1px solid #D4AF37',
                      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)'
                    }}>
                      <Typography variant="subtitle2" sx={{ color: '#D4AF37' }}>Volatility</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 'bold', mt: 1, color: '#F5F5DC' }}>
                        {portfolioSummary?.risk_metrics?.volatility?.toFixed(2) || '0.00'}%
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#D4AF37' }}>
                        {portfolioSummary?.risk_metrics?.volatility && portfolioSummary.risk_metrics.volatility > 15 ? 'High volatility' : 'Low volatility'}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Asset Allocation Chart */}
          <Grid item xs={12} md={6}>
            <Card 
              elevation={3} 
              sx={{ 
                borderRadius: 2,
                height: '100%',
                background: 'rgba(0, 0, 0, 0.7)',
                border: '1px solid #D4AF37',
                transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-5px)',
                  boxShadow: '0 12px 20px rgba(0, 0, 0, 0.3)'
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h5" component="div" sx={{ ...renaissanceTitleStyle, color: '#D4AF37' }}>
                    Asset Allocation
                  </Typography>
                  <Tooltip title="Distribution of your investments across different asset types">
                    <IconButton size="small" sx={{ ml: 1, color: '#D4AF37' }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Divider sx={renaissanceDividerStyle} />
                <Box sx={{ height: 300 }}>
                  {assetAllocationData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={assetAllocationData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        >
                          {assetAllocationData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <RechartsTooltip 
                          formatter={(value) => formatPercentage(value as number)}
                          contentStyle={{ 
                            backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                            border: '1px solid #D4AF37',
                            borderRadius: '4px',
                            color: '#F5F5DC'
                          }}
                        />
                        <Legend 
                          wrapperStyle={{ color: '#F5F5DC' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Typography variant="body1" sx={{ color: '#D4AF37' }}>
                        No assets to display
                      </Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Asset Allocation Bar Chart */}
          <Grid item xs={12}>
            <Card 
              elevation={3} 
              sx={{ 
                borderRadius: 2,
                background: 'rgba(0, 0, 0, 0.7)',
                border: '1px solid #D4AF37',
                transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-5px)',
                  boxShadow: '0 12px 20px rgba(0, 0, 0, 0.3)'
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h5" component="div" sx={{ ...renaissanceTitleStyle, color: '#D4AF37' }}>
                    Asset Allocation Details
                  </Typography>
                  <Tooltip title="Detailed breakdown of your portfolio allocation">
                    <IconButton size="small" sx={{ ml: 1, color: '#D4AF37' }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Divider sx={renaissanceDividerStyle} />
                <Box sx={{ height: 300 }}>
                  {assetAllocationData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={assetAllocationData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#D4AF37" opacity={0.2} />
                        <XAxis 
                          dataKey="name" 
                          tick={{ fill: '#F5F5DC' }}
                          axisLine={{ stroke: '#D4AF37' }}
                        />
                        <YAxis 
                          tickFormatter={(value) => `${value}%`} 
                          tick={{ fill: '#F5F5DC' }}
                          axisLine={{ stroke: '#D4AF37' }}
                        />
                        <RechartsTooltip 
                          formatter={(value) => formatPercentage(value as number)}
                          labelFormatter={(label) => `${label}`}
                          contentStyle={{ 
                            backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                            border: '1px solid #D4AF37',
                            borderRadius: '4px',
                            color: '#F5F5DC'
                          }}
                        />
                        <Legend 
                          wrapperStyle={{ color: '#F5F5DC' }}
                        />
                        <Bar 
                          dataKey="value" 
                          name="Allocation (%)" 
                          fill="#D4AF37"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Typography variant="body1" sx={{ color: '#D4AF37' }}>
                        No assets to display
                      </Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        
        {/* Decorative footer */}
        <Box sx={{ 
          mt: 4, 
          textAlign: 'center',
          position: 'relative',
          '&::before, &::after': {
            content: '""',
            position: 'absolute',
            top: '50%',
            width: '30%',
            height: '1px',
            background: 'linear-gradient(90deg, transparent, #D4AF37, transparent)',
          },
          '&::before': {
            left: 0
          },
          '&::after': {
            right: 0
          }
        }}>
          <Typography variant="body2" sx={{ color: '#D4AF37', fontStyle: 'italic' }}>
            "Fortuna favet fortibus" - Fortune favors the bold
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default Dashboard; 