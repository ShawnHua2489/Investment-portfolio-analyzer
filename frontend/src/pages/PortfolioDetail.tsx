import React from 'react';
import { useParams } from 'react-router-dom';
import { Grid, Paper, Typography, Box, Button } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import AddIcon from '@mui/icons-material/Add';

interface Asset {
  id: string;
  symbol: string;
  name: string;
  quantity: number;
  purchase_price: number;
  current_price: number;
  total_value: number;
  asset_type: string;
}

interface PortfolioDetail {
  id: string;
  name: string;
  total_value: number;
  assets: Asset[];
  asset_allocation: Record<string, number>;
  risk_metrics: {
    beta: number;
    sharpe_ratio: number;
    volatility: number;
  };
  performance_history: {
    date: string;
    value: number;
  }[];
}

const PortfolioDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { data: portfolio, isLoading, error } = useQuery<PortfolioDetail>(
    ['portfolio', id],
    async () => {
      const response = await axios.get(`http://localhost:8000/api/v1/portfolios/${id}`);
      return response.data;
    }
  );

  const columns: GridColDef[] = [
    { field: 'symbol', headerName: 'Symbol', flex: 1 },
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'asset_type', headerName: 'Type', flex: 1 },
    { field: 'quantity', headerName: 'Quantity', flex: 1 },
    {
      field: 'purchase_price',
      headerName: 'Purchase Price',
      flex: 1,
      valueFormatter: (params) => {
        const value = params.value as number;
        return value ? `$${value.toFixed(2)}` : '$0.00';
      },
    },
    {
      field: 'current_price',
      headerName: 'Current Price',
      flex: 1,
      valueFormatter: (params) => {
        const value = params.value as number;
        return value ? `$${value.toFixed(2)}` : '$0.00';
      },
    },
    {
      field: 'total_value',
      headerName: 'Total Value',
      flex: 1,
      valueFormatter: (params) => {
        const value = params.value as number;
        return value ? `$${value.toLocaleString()}` : '$0';
      },
    },
  ];

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  if (error) {
    return <Typography color="error">Error loading portfolio: {error instanceof Error ? error.message : 'Unknown error'}</Typography>;
  }

  if (!portfolio) {
    return <Typography>Portfolio not found</Typography>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">{portfolio.name}</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => {/* TODO: Implement add asset */}}
        >
          Add Asset
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Assets</Typography>
            <Box sx={{ height: 400, width: '100%' }}>
              <DataGrid
                rows={portfolio.assets || []}
                columns={columns}
                getRowId={(row) => `${row.symbol}-${row.purchase_date}`}
                initialState={{
                  pagination: {
                    paginationModel: { pageSize: 10 },
                  },
                }}
                pageSizeOptions={[10]}
                disableRowSelectionOnClick
              />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Performance</Typography>
            <Box sx={{ height: 400, width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={portfolio.performance_history || []}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Risk Metrics</Typography>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography variant="subtitle2">Beta</Typography>
                <Typography variant="h6">{portfolio.risk_metrics?.beta?.toFixed(2) || 'N/A'}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="subtitle2">Sharpe Ratio</Typography>
                <Typography variant="h6">{portfolio.risk_metrics?.sharpe_ratio?.toFixed(2) || 'N/A'}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="subtitle2">Volatility</Typography>
                <Typography variant="h6">{portfolio.risk_metrics?.volatility?.toFixed(2) || 'N/A'}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PortfolioDetail; 