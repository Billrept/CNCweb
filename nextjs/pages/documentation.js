import { Container, Box, Typography } from '@mui/material';

export default function Documentation() {
  return (
    <Box sx={{ py: 8 }}>
      <Container>
        <Typography variant="h4" gutterBottom>
          Documentation
        </Typography>
        <Typography paragraph>
          Welcome to the documentation for the 3-in-1 CNC machine. Here you'll find setup instructions, user guides, and troubleshooting tips.
        </Typography>
        <Typography paragraph>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus lacinia odio vitae vestibulum vestibulum.
        </Typography>
      </Container>
    </Box>
  );
}
