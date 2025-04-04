import React, { useState } from 'react';
import { Box, Typography, TextField, Button, Paper, Alert, FormHelperText } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from 'react-query';
import axios from 'axios';

const CreatePortfolio: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  const createPortfolioMutation = useMutation(
    async (portfolioData: { name: string; description: string }) => {
      try {
        const response = await axios.post('http://localhost:8000/api/v1/portfolios/', portfolioData);
        return response.data;
      } catch (err) {
        if (axios.isAxiosError(err)) {
          setError(err.response?.data?.detail || 'Failed to create portfolio');
        } else {
          setError('An unexpected error occurred');
        }
        throw err;
      }
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('portfolios');
        navigate('/portfolios');
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Validate inputs
    if (!name.trim()) {
      setError('Portfolio name is required');
      return;
    }
    
    if (name.length < 3) {
      setError('Portfolio name must be at least 3 characters long');
      return;
    }
    
    createPortfolioMutation.mutate({ name, description });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Create New Portfolio
      </Typography>
      
      <Paper sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
        <Typography variant="body1" paragraph>
          A portfolio helps you track and manage your investments. Give your portfolio a descriptive name 
          and add details about your investment strategy or goals.
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Portfolio Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            margin="normal"
            required
            helperText="Choose a descriptive name that reflects your investment strategy (e.g., 'Growth Portfolio', 'Retirement Fund')"
          />
          
          <TextField
            fullWidth
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            margin="normal"
            multiline
            rows={4}
            helperText="Describe your investment goals, risk tolerance, or specific strategies for this portfolio"
          />
          
          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              color="primary"
              type="submit"
              disabled={createPortfolioMutation.isLoading}
            >
              {createPortfolioMutation.isLoading ? 'Creating...' : 'Create Portfolio'}
            </Button>
            <Button
              variant="outlined"
              onClick={() => navigate('/portfolios')}
            >
              Cancel
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default CreatePortfolio; 