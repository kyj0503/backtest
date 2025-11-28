import React from 'react';
import {
  HeroSection,
  WhatIsBacktestSection,
  HowToUseSection,
  KeyFeaturesSection,
  CTASection,
} from './landing';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <WhatIsBacktestSection />
      <HowToUseSection />
      <KeyFeaturesSection />
      <CTASection />
    </div>
  );
};

export default HomePage;
