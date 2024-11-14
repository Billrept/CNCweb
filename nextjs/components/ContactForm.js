import { Box, Container, Typography, TextField, Button } from '@mui/material';
import { useState } from 'react';

export default function ContactForm() {
  const [contactInfo, setContactInfo] = useState({ name: '', email: '', message: '' });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setContactInfo((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    alert('Message sent!');
  };

  return (
    <Box id="contactForm" sx={{ py: 8, backgroundColor: 'background.default' }}>
      <Container>
        <Typography variant="h4" align="center" color="secondary" gutterBottom>
          Contact Us
        </Typography>
        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 600, mx: 'auto' }}
        >
          <TextField label="Your Name" name="name" value={contactInfo.name} onChange={handleChange} required color="secondary" />
          <TextField label="Your Email" name="email" type="email" value={contactInfo.email} onChange={handleChange} required color="secondary" />
          <TextField
            label="Your Message"
            name="message"
            value={contactInfo.message}
            onChange={handleChange}
            multiline
            rows={4}
            required
            color="secondary"
          />
          <Button type="submit" variant="contained" color="secondary">
            Send
          </Button>
        </Box>
      </Container>
    </Box>
  );
}
