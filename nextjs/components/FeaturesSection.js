import { Box, Container, Typography } from '@mui/material';
import { motion } from 'framer-motion';

const featureVariants = {
  hidden: { opacity: 0, y: 50 },
  visible: { opacity: 1, y: 0 },
};

export default function FeatureSection({ title, description, bgColor }) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.5 }}
      variants={featureVariants}
      transition={{ duration: 0.6 }}
    >
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: bgColor,
          color: 'secondary.main',
          textAlign: 'center',
          padding: 4,
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h3" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h6" color="textSecondary" paragraph>
            {description}
          </Typography>
        </Container>
      </Box>
    </motion.div>
  );
}
