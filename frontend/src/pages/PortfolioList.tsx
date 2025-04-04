import React, { useState } from 'react';
import { Box, Typography, Button, IconButton, Tooltip } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import EditPortfolioDialog from '../components/EditPortfolioDialog';

interface Portfolio {
  id: string;
  name: string;
  description: string;
  total_value: number;
  asset_count: number;
  created_at: string;
  updated_at: string;
}

const PortfolioList = () => {
  const navigate = useNavigate();
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  
  const { data: portfolios, isLoading, error } = useQuery<Portfolio[]>(
    'portfolios',
    async () => {
      const response = await axios.get('http://localhost:8000/api/v1/portfolios/');
      return response.data;
    }
  );

  const handleEditClick = (portfolio: Portfolio) => {
    setSelectedPortfolio(portfolio);
    setEditDialogOpen(true);
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  if (error) {
    return <Typography color="error">Error loading portfolios: {error instanceof Error ? error.message : 'Unknown error'}</Typography>;
  }

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'Name', flex: 1 },
    {
      field: 'total_value',
      headerName: 'Total Value',
      flex: 1,
      valueFormatter: (params) => {
        const value = params.value as number;
        return value ? `$${value.toLocaleString()}` : '$0';
      },
    },
    { field: 'asset_count', headerName: 'Assets', flex: 1 },
    {
      field: 'created_at',
      headerName: 'Created',
      flex: 1,
      valueFormatter: (params) => {
        const date = params.value as string;
        return date ? new Date(date).toLocaleDateString() : '';
      },
    },
    {
      field: 'updated_at',
      headerName: 'Last Updated',
      flex: 1,
      valueFormatter: (params) => {
        const date = params.value as string;
        return date ? new Date(date).toLocaleDateString() : '';
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      flex: 1,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Edit Portfolio">
            <IconButton
              color="primary"
              onClick={() => handleEditClick(params.row)}
            >
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate(`/portfolios/${params.row.id}`)}
          >
            View Details
          </Button>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Portfolios</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => navigate('/portfolios/new')}
        >
          Create Portfolio
        </Button>
      </Box>

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={portfolios || []}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 10 },
            },
          }}
          pageSizeOptions={[10]}
          loading={isLoading}
          disableRowSelectionOnClick
        />
      </Box>
      
      {selectedPortfolio && (
        <EditPortfolioDialog
          open={editDialogOpen}
          onClose={() => {
            setEditDialogOpen(false);
            setSelectedPortfolio(null);
          }}
          portfolio={selectedPortfolio}
        />
      )}
    </Box>
  );
};

export default PortfolioList; 