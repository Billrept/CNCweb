import HeroSection from '../components/HeroSection';
import FeatureSection from '../components/FeaturesSection';
import Highlights from '../components/Highlights';
import ContactForm from '../components/ContactForm';
import Footer from '../components/Footer';

export default function Home() {
  return (
    <>
      <HeroSection />
      <FeatureSection
        title="Drawing"
        description="Create intricate designs with precision drawing."
        bgColor="#1d1d1d"
      />
      <FeatureSection
        title="CNC Drilling"
        description="Experience accurate drilling with our CNC technology."
        bgColor="#121212"
      />
      <FeatureSection
        title="Laser Engraving"
        description="Engrave on various materials with high precision."
        bgColor="#1d1d1d"
      />
      <Highlights />
      <ContactForm /> {/* Contact form with the target id="contactForm" */}
      <Footer />
    </>
  );
}