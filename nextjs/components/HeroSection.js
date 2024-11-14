import { Box, Container, Typography, Button } from '@mui/material';

export default function HeroSection() {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'primary.main',
        color: 'secondary.main',
        textAlign: 'center',
      }}
    >
      <Container maxWidth="md">
        <Typography variant="h2" gutterBottom>
          Transform Your Ideas with Our 3-in-1 CNC Machine
        </Typography>
        <Typography variant="h5" color="textSecondary" paragraph>
          Experience the power of laser engraving, CNC drilling, and drawing in one device.
        </Typography>
        <Button variant="contained" color="secondary" size="large">
          Learn More
        </Button>
      </Container>
    </Box>
  );
}
