import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useState, useEffect } from 'react';
import { scroller } from 'react-scroll';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 50) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleGetStartedClick = () => {
    if (router.pathname === '/') {
      scroller.scrollTo('contactForm', {
        smooth: true,
        duration: 500,
        offset: -70,
      });
    } else {
      router.push('/').then(() => {
        scroller.scrollTo('contactForm', {
          smooth: true,
          duration: 500,
          offset: -70,
        });
      });
    }
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        backgroundColor: scrolled ? 'rgba(18, 18, 18, 0.95)' : 'transparent',
        transition: 'background-color 0.3s ease',
        color: '#FFFFFF',
        boxShadow: 'none',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: 3 }}>
        {/* Logo */}
        <Box display="flex" alignItems="center">
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mr: 2 }}>
            MaeJoo CNC
          </Typography>
        </Box>

        {/* Navigation Links */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 3 }}>
          <Link href="/" passHref>
            <Button
              color="inherit"
              sx={{
                color: '#FFFFFF',
                '&:hover': {
                  color: '#00FF00',
                },
              }}
            >
              Products
            </Button>
          </Link>
          <Link href="/documentation" passHref>
            <Button
              color="inherit"
              sx={{
                color: '#FFFFFF',
                '&:hover': {
                  color: '#00FF00',
                },
              }}
            >
              Documentation
            </Button>
          </Link>
          <Link href="/converter" passHref>
            <Button
              color="inherit"
              sx={{
                color: '#FFFFFF',
                '&:hover': {
                  color: '#00FF00',
                },
              }}
            >
              Converter
            </Button>
          </Link>
        </Box>

        {/* "Get Started" Button */}
        <Box>
          <Button
            variant="outlined"
            color="inherit"
            onClick={handleGetStartedClick}
            sx={{
              borderColor: '#FFFFFF',
              color: '#FFFFFF',
              '&:hover': {
                borderColor: '#00FF00',
                color: '#00FF00',
              },
            }}
          >
            Get Started
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
