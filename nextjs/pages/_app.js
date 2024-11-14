import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Header from '../components/Header';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#000000',
    },
    secondary: {
      main: '#00FF00',
    },
    background: {
      default: '#121212',
      paper: '#1d1d1d',
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#A0A0A0',
    },
  },
  typography: {
    fontFamily: 'Roboto, sans-serif',
  },
});

function MyApp({ Component, pageProps }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Header />
      {/* Adds padding to prevent content overlap with the fixed header */}
      <Box sx={{ paddingTop: '64px' }}>
        <Component {...pageProps} />
      </Box>
    </ThemeProvider>
  );
}

export default MyApp;
