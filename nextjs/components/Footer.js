import { Box, Container, Typography } from '@mui/material';

export default function Footer() {
  return (
    <Box sx={{ py: 4, backgroundColor: 'primary.main', textAlign: 'center' }}>
      <Container>
        <Typography variant="body2" color="textSecondary">
          &copy; {new Date().getFullYear()} MaeJoo CNC Machine
        </Typography>
      </Container>
    </Box>
  );
}
