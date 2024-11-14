import { Box, Container, Typography, Grid, Paper } from '@mui/material';
import { motion } from 'framer-motion';

export default function Highlights() {
  const highlights = [
    { title: 'Precision', value: '0.01mm' },
    { title: 'Power', value: '500W' },
    { title: 'Speed', value: '1200mm/s' },
  ];

  return (
    <Box sx={{ py: 8, backgroundColor: 'background.paper' }}>
      <Container>
        <Typography variant="h4" align="center" color="secondary" gutterBottom>
          Key Highlights
        </Typography>
        <Grid container spacing={4} justifyContent="center">
          {highlights.map((highlight, index) => (
            <Grid item xs={12} sm={4} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5 }}
              >
                <Paper
                  elevation={3}
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    backgroundColor: 'primary.main',
                    color: 'secondary.main',
                  }}
                >
                  <Typography variant="h5">{highlight.value}</Typography>
                  <Typography variant="body1" color="textSecondary">
                    {highlight.title}
                  </Typography>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
