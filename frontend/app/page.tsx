import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import FeatureCards from "@/components/FeatureCards";
import TechnologyPipeline from "@/components/TechnologyPipeline";
import UploadSection from "@/components/UploadSection";
import Footer from "@/components/Footer";
import PageTransition from "@/components/ui/PageTransition";

export default function Home() {
  return (
    <PageTransition>
      <main className="min-h-screen overflow-x-hidden bg-[#0C0F0F] text-white">
        <Navbar />
        <Hero />
        <UploadSection />
        <FeatureCards />
        <TechnologyPipeline />
        <Footer />
      </main>
    </PageTransition>
  );
}
