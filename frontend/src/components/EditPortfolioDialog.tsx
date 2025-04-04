import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField, 
  Button,
  Alert
} from '@mui/material';
import { useMutation, useQueryClient } from 'react-query';
import axios from 'axios';

interface EditPortfolioDialogProps {
  open: boolean;
  onClose: () => void;
  portfolio: {
    id: string;
    name: string;
    description: string;
  };
}

const EditPortfolioDialog: React.FC<EditPortfolioDialogProps> = ({ open, onClose, portfolio }) => {
  const queryClient = useQueryClient();
  const [name, setName] = useState(portfolio.name);
  const [description, setDescription] = useState(portfolio.description);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(portfolio.name);
    setDescription(portfolio.description);
  }, [portfolio]);

  const updatePortfolioMutation = useMutation(
    async (data: { name: string; description: string }) => {
      try {
        const response = await axios.put(`http://localhost:8000/api/v1/portfolios/${portfolio.id}`, data);
        return response.data;
      } catch (err) {
        if (axios.isAxiosError(err)) {
          setError(err.response?.data?.detail || 'Failed to update portfolio');
        } else {
          setError('An unexpected error occurred');
        }
        throw err;
      }
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('portfolios');
        onClose();
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
    
    updatePortfolioMutation.mutate({ name, description });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>Edit Portfolio</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            fullWidth
            label="Portfolio Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            margin="normal"
            required
            helperText="Choose a descriptive name that reflects your investment strategy"
          />
          
          <TextField
            fullWidth
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            margin="normal"
            multiline
            rows={4}
            helperText="Describe your investment goals, risk tolerance, or specific strategies"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button 
            type="submit" 
            variant="contained" 
            color="primary"
            disabled={updatePortfolioMutation.isLoading}
          >
            {updatePortfolioMutation.isLoading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default EditPortfolioDialog; 