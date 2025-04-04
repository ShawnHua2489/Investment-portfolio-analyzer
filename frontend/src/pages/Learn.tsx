import React from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box, 
  Accordion, 
  AccordionSummary, 
  AccordionDetails, 
  List, 
  ListItem, 
  ListItemText,
  ListItemIcon,
  Chip,
  useTheme
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { useQuery } from 'react-query';
import axios from 'axios';

interface EducationalContent {
  description: string;
  categories: {
    name: string;
    examples: string[];
    benefits: string[];
    typical_allocation: string;
  }[];
  investment_methods: {
    method: string;
    description: string;
    advantages: string[];
  }[];
  risks: string[];
  portfolio_integration: string[];
}

const Learn = () => {
  const theme = useTheme();

  const { data: etfsContent, isLoading: etfsLoading } = useQuery<EducationalContent>(
    'etfs',
    async () => {
      const response = await axios.get('http://localhost:8000/api/v1/learn/etfs');
      return response.data;
    }
  );

  const { data: stocksContent, isLoading: stocksLoading } = useQuery<EducationalContent>(
    'stocks',
    async () => {
      const response = await axios.get('http://localhost:8000/api/v1/learn/stocks');
      return response.data;
    }
  );

  const { data: bondsContent, isLoading: bondsLoading } = useQuery<EducationalContent>(
    'bonds',
    async () => {
      const response = await axios.get('http://localhost:8000/api/v1/learn/bonds');
      return response.data;
    }
  );

  if (etfsLoading || stocksLoading || bondsLoading) {
    return <Typography>Loading...</Typography>;
  }

  const renderAssetContent = (title: string, content: EducationalContent | undefined) => (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 4, 
        mb: 4,
        borderRadius: 2,
        backgroundColor: theme.palette.background.paper,
      }}
    >
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom color="primary">
          {title}
        </Typography>
        <Typography 
          variant="subtitle1" 
          paragraph 
          sx={{ 
            color: theme.palette.text.secondary,
            fontSize: '1.1rem',
            lineHeight: 1.6 
          }}
        >
          {content?.description || 'Content not available'}
        </Typography>
      </Box>

      <Accordion 
        defaultExpanded 
        sx={{ 
          mb: 2,
          '&:before': { display: 'none' },
          boxShadow: 'none',
          backgroundColor: 'transparent'
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            backgroundColor: theme.palette.primary.main,
            color: '#7393B3',
            borderRadius: 1,
            '& .MuiAccordionSummary-content': {
              color: '#7393B3',
              fontWeight: 'bold'
            }
          }}
        >
          <Typography variant="h6">Categories</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            {content?.categories?.map((category) => (
              <Grid item xs={12} md={6} key={category.name}>
                <Paper 
                  sx={{ 
                    p: 3,
                    height: '100%',
                    borderRadius: 2,
                    border: `1px solid ${theme.palette.divider}`,
                    '&:hover': {
                      boxShadow: theme.shadows[4]
                    },
                    transition: 'box-shadow 0.3s ease-in-out'
                  }}
                >
                  <Typography 
                    variant="h6" 
                    gutterBottom 
                    color="primary"
                    sx={{ fontWeight: 'bold' }}
                  >
                    {category.name}
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom color="textSecondary">
                      Examples:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {category.examples?.map((example) => (
                        <Chip 
                          key={example} 
                          label={example} 
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                  <Typography variant="subtitle2" gutterBottom color="textSecondary">
                    Benefits:
                  </Typography>
                  <List dense>
                    {category.benefits?.map((benefit) => (
                      <ListItem key={benefit} disableGutters>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <CheckCircleOutlineIcon color="primary" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={benefit}
                          primaryTypographyProps={{
                            variant: 'body2',
                            color: 'textPrimary'
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                  <Box sx={{ mt: 2 }}>
                    <Chip
                      label={`Typical Allocation: ${category.typical_allocation}`}
                      color="secondary"
                      icon={<TrendingUpIcon />}
                    />
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </AccordionDetails>
      </Accordion>

      <Accordion 
        sx={{ 
          mb: 2,
          '&:before': { display: 'none' },
          boxShadow: 'none',
          backgroundColor: 'transparent'
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{
            backgroundColor: theme.palette.secondary.main,
            color: '#7393B3',
            borderRadius: 1,
            '& .MuiAccordionSummary-content': {
              color: '#7393B3',
              fontWeight: 'bold'
            }
          }}
        >
          <Typography variant="h6">Investment Methods</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            {content?.investment_methods?.map((method) => (
              <Grid item xs={12} md={4} key={method.method}>
                <Paper 
                  sx={{ 
                    p: 3,
                    height: '100%',
                    borderRadius: 2,
                    border: `1px solid ${theme.palette.divider}`,
                    '&:hover': {
                      boxShadow: theme.shadows[4]
                    },
                    transition: 'box-shadow 0.3s ease-in-out'
                  }}
                >
                  <Typography 
                    variant="h6" 
                    gutterBottom 
                    color="secondary"
                    sx={{ fontWeight: 'bold' }}
                  >
                    {method.method}
                  </Typography>
                  <Typography 
                    paragraph 
                    variant="body2" 
                    color="textSecondary"
                  >
                    {method.description}
                  </Typography>
                  <Typography variant="subtitle2" gutterBottom color="textSecondary">
                    Advantages:
                  </Typography>
                  <List dense>
                    {method.advantages?.map((advantage) => (
                      <ListItem key={advantage} disableGutters>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <CheckCircleOutlineIcon color="secondary" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={advantage}
                          primaryTypographyProps={{
                            variant: 'body2',
                            color: 'textPrimary'
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </AccordionDetails>
      </Accordion>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Accordion 
            sx={{ 
              '&:before': { display: 'none' },
              boxShadow: 'none',
              backgroundColor: 'transparent'
            }}
          >
            <AccordionSummary 
              expandIcon={<ExpandMoreIcon />}
              sx={{
                backgroundColor: theme.palette.error.main,
                color: '#7393B3',
                borderRadius: 1,
                '& .MuiAccordionSummary-content': {
                  color: '#7393B3',
                  fontWeight: 'bold'
                }
              }}
            >
              <Typography variant="h6">Risks</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Paper 
                sx={{ 
                  p: 3,
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                <List>
                  {content?.risks?.map((risk) => (
                    <ListItem key={risk}>
                      <ListItemIcon>
                        <CheckCircleOutlineIcon color="error" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={risk}
                        primaryTypographyProps={{
                          color: 'textPrimary'
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </AccordionDetails>
          </Accordion>
        </Grid>

        <Grid item xs={12} md={6}>
          <Accordion 
            sx={{ 
              '&:before': { display: 'none' },
              boxShadow: 'none',
              backgroundColor: 'transparent'
            }}
          >
            <AccordionSummary 
              expandIcon={<ExpandMoreIcon />}
              sx={{
                backgroundColor: theme.palette.success.main,
                color: '#7393B3',
                borderRadius: 1,
                '& .MuiAccordionSummary-content': {
                  color: '#7393B3',
                  fontWeight: 'bold'
                }
              }}
            >
              <Typography variant="h6">Portfolio Integration</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Paper 
                sx={{ 
                  p: 3,
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                <List>
                  {content?.portfolio_integration?.map((tip) => (
                    <ListItem key={tip}>
                      <ListItemIcon>
                        <CheckCircleOutlineIcon color="success" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={tip}
                        primaryTypographyProps={{
                          color: 'textPrimary'
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </AccordionDetails>
          </Accordion>
        </Grid>
      </Grid>
    </Paper>
  );

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography 
        variant="h3" 
        gutterBottom 
        align="center"
        sx={{ 
          mb: 4,
          fontWeight: 'bold',
          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}
      >
        Investment Education
      </Typography>
      {renderAssetContent('ETFs', etfsContent)}
      {renderAssetContent('Stocks', stocksContent)}
      {renderAssetContent('Bonds', bondsContent)}
    </Box>
  );
};

export default Learn; 