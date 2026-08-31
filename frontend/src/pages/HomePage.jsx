import HomeNavbar from "../components/home/HomeNavbar";
import HeroSection from "../components/home/HeroSection";
import WhatItDoes from "../components/home/WhatItDoes";
import AgentNetwork from "../components/home/AgentNetwork";
import RepositoryIntelligence from "../components/home/RepositoryIntelligence";
import LiveProductPreview from "../components/home/LiveProductPreview";
import PricingPreview from "../components/home/PricingPreview";
import HowItWorks from "../components/home/HowItWorks";
import FinalCTA from "../components/home/FinalCTA";
import HomeFooter from "../components/home/HomeFooter";
import "../components/home/home.css";

export default function HomePage() {
  return (
    <div className="di-home">
      <div className="di-atmosphere" aria-hidden="true">
        <span className="di-veil di-veil-a" />
        <span className="di-veil di-veil-b" />
        <span className="di-veil di-veil-c" />
        <span className="di-scan" />
        <span className="di-grain" />
      </div>
      <HomeNavbar />
      <main id="di-main" className="di-page-enter">
        <HeroSection />
        <WhatItDoes />
        <AgentNetwork />
        <RepositoryIntelligence />
        <LiveProductPreview />
        <PricingPreview />
        <HowItWorks />
        <FinalCTA />
      </main>
      <HomeFooter />
    </div>
  );
}
