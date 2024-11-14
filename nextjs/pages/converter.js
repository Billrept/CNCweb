import { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardHeader,
  CardContent,
  TextField,
  MenuItem,
  Button,
  CircularProgress,
  Link as MuiLink,
  Backdrop,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';

export default function Converter() {
  const [formData, setFormData] = useState({
    mode: 'drilling',
    laser_power: 1000,
    speed: 900,
    pass_depth: 5,
  });
  const [svgFile, setSvgFile] = useState(null);
  const [svgPreviewUrl, setSvgPreviewUrl] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState('');

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setDownloadUrl('');

    const data = new FormData();
    data.append('svg_file', svgFile);
    data.append('mode', formData.mode);
    data.append('laser_power', formData.laser_power);
    data.append('speed', formData.speed);
    data.append('pass_depth', formData.pass_depth);

    try {
      const response = await fetch('/api/convert', {
        method: 'POST',
        body: data,
      });
      const result = await response.json();
      setProcessing(false);

      if (result.success) {
        setDownloadUrl(result.download_url);
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
          title="MultiSVG: SVG to G-code Converter"
          sx={{
            backgroundColor: 'primary.main',
            color: 'secondary.main',
            textAlign: 'center',
            py: 2,
          }}
        />
        <CardContent>
          <Box component="form" onSubmit={handleSubmit} noValidate autoComplete="off">
            <TextField
              select
              fullWidth
              label="Mode"
              name="mode"
              value={formData.mode}
              onChange={handleInputChange}
              margin="normal"
              color="secondary"
            >
              <MenuItem value="drilling">Drilling/Engraving</MenuItem>
              <MenuItem value="drawing">Drawing</MenuItem>
            </TextField>
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
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="textSecondary">
                  SVG Preview:
                </Typography>
                <img src={svgPreviewUrl} alt="SVG Preview" style={{ width: '100%', maxHeight: '300px' }} />
              </Box>
            )}
            <TextField
              label="Laser Power"
              name="laser_power"
              type="number"
              fullWidth
              value={formData.laser_power}
              onChange={handleInputChange}
              margin="normal"
              color="secondary"
            />
            <TextField
              label="Speed"
              name="speed"
              type="number"
              fullWidth
              value={formData.speed}
              onChange={handleInputChange}
              margin="normal"
              color="secondary"
            />
            <TextField
              label="Pass Depth"
              name="pass_depth"
              type="number"
              fullWidth
              value={formData.pass_depth}
              onChange={handleInputChange}
              margin="normal"
              color="secondary"
            />
            <Button type="submit" variant="contained" color="secondary" fullWidth sx={{ mt: 3 }} disabled={processing}>
              Convert to G-code
            </Button>
          </Box>

          {/* Fixed overlay spinner for processing */}
          <Backdrop open={processing} sx={{ color: '#00FF00', zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <CircularProgress color="inherit" />
            <Typography variant="h6" sx={{ ml: 2 }}>Processing...</Typography>
          </Backdrop>

          {/* Enhanced download button */}
          {downloadUrl && (
            <Box textAlign="center" sx={{ mt: 3 }}>
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
