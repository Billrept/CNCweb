import { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardHeader,
  CardContent,
  TextField,
  Button,
  CircularProgress,
  Link as MuiLink,
  Backdrop,
  IconButton,
  Paper,
  Chip,
  Stack,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';
import CloseIcon from '@mui/icons-material/Close';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PaletteIcon from '@mui/icons-material/Palette';

export default function Converter() {
  const [formData, setFormData] = useState({
    speed: 155,
  });
  const [svgFile, setSvgFile] = useState(null);
  const [svgPreviewUrl, setSvgPreviewUrl] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState('');
  const [processingTime, setProcessingTime] = useState(null);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [detectedColors, setDetectedColors] = useState([]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSvgFile(file);

    // Create a URL for SVG preview
    if (file) {
      const previewUrl = URL.createObjectURL(file);
      setSvgPreviewUrl(previewUrl);
    }
  };
  
  // Function to clear the selected file
  const handleClearFile = () => {
    if (svgPreviewUrl) {
      URL.revokeObjectURL(svgPreviewUrl);
    }
    setSvgFile(null);
    setSvgPreviewUrl(null);
    setDownloadUrl('');
    setProcessingTime(null);
    setDetectedColors([]);
  };
  
  // Effect to handle the timer
  useEffect(() => {
    let intervalId = null;
    
    if (processing) {
      // Start a timer that increments every 100ms
      intervalId = setInterval(() => {
        setTimeElapsed(prev => prev + 0.1);
      }, 100);
    }
    
    // Cleanup on unmount or when processing changes
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [processing]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setDownloadUrl('');
    setProcessingTime(null);
    setTimeElapsed(0);
    setDetectedColors([]);

    const data = new FormData();
    data.append('svg_file', svgFile);
    data.append('speed', formData.speed);
    
    try {
      const response = await fetch('/api/convert', {
        method: 'POST',
        body: data,
      });
      const result = await response.json();
      setProcessing(false);

      if (result.success) {
        setDownloadUrl(result.download_url);
        setProcessingTime(result.processing_time);
      } else {
        alert(result.message || 'An error occurred while processing the file.');
      }
    } catch (error) {
      setProcessing(false);
      alert('An error occurred while processing the file.');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 5 }}>
      <Card sx={{ boxShadow: 3, backgroundColor: 'background.paper' }}>
        <CardHeader
          title="SVG to G-code Drawing Converter"
          sx={{
            backgroundColor: 'primary.main',
            color: 'secondary.main',
            textAlign: 'center',
            py: 2,
          }}
        />
        <CardContent>
          <Box component="form" onSubmit={handleSubmit} noValidate autoComplete="off">
            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadFileIcon />}
              fullWidth
              sx={{ mt: 2 }}
              color="secondary"
            >
              Upload SVG File
              <input type="file" hidden accept=".svg" onChange={handleFileChange} required />
            </Button>
            
            {svgPreviewUrl && (
              <Box sx={{ mt: 2, textAlign: 'center', position: 'relative' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="textSecondary">
                    SVG Preview:
                  </Typography>
                  <IconButton onClick={handleClearFile} size="small" color="secondary">
                    <CloseIcon />
                  </IconButton>
                </Box>
                <img src={svgPreviewUrl} alt="SVG Preview" style={{ width: '100%', maxHeight: '300px' }} />
              </Box>
            )}
            
            <TextField
              label="Speed (mm/min)"
              name="speed"
              type="number"
              fullWidth
              value={formData.speed}
              onChange={handleInputChange}
              margin="normal"
              color="secondary"
              helperText="Drawing speed in mm/min"
            />
            
            <Button 
              type="submit" 
              variant="contained" 
              color="secondary" 
              fullWidth 
              sx={{ mt: 3 }} 
              disabled={processing || !svgFile}
            >
              Convert to G-code
            </Button>
          </Box>

          {/* Processing indicator */}
          <Backdrop open={processing} sx={{ color: '#00FF00', zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Paper elevation={3} sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: 'rgba(0, 0, 0, 0.7)', borderRadius: 2 }}>
              <CircularProgress color="inherit" size={60} />
              <Typography variant="h5" sx={{ mt: 2, color: '#00FF00' }}>Processing...</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                <AccessTimeIcon sx={{ mr: 1, color: '#00FF00' }} />
                <Typography variant="h6" sx={{ color: '#00FF00' }}>
                  Time elapsed: {timeElapsed.toFixed(1)}s
                </Typography>
              </Box>
            </Paper>
          </Backdrop>

          {/* Download button */}
          {downloadUrl && (
            <Box textAlign="center" sx={{ mt: 3 }}>
              {processingTime && (
                <Paper elevation={1} sx={{ p: 1, mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'primary.dark' }}>
                  <AccessTimeIcon sx={{ mr: 1, color: 'secondary.main' }} />
                  <Typography variant="body2" color="secondary.main">
                    Processed in {processingTime} seconds
                  </Typography>
                </Paper>
              )}
              <MuiLink href={downloadUrl} target="_blank" rel="noopener noreferrer" sx={{ textDecoration: 'none' }}>
                <Button variant="contained" color="secondary" fullWidth startIcon={<DownloadIcon />}>
                  Download G-code
                </Button>
              </MuiLink>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
}
