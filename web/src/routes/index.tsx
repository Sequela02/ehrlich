import { createFileRoute } from "@tanstack/react-router";
import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { ConsolePreview } from "@/components/ConsolePreview";
import { Architecture } from "@/components/Architecture";
import { Domains } from "@/components/Domains";
import { Visualizations } from "@/components/Visualizations";
import { DataSources } from "@/components/DataSources";
import { WhoItsFor } from "@/components/WhoItsFor";
import { Differentiators } from "@/components/Differentiators";
import { OpenSource } from "@/components/OpenSource";
import { Roadmap } from "@/components/Roadmap";
import { CTA } from "@/components/CTA";
import { Footer } from "@/components/Footer";

export const Route = createFileRoute("/")({
  component: LandingPage,
});

function LandingPage() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <HowItWorks />
        <ConsolePreview />
        <Architecture />
        <Domains />
        <Visualizations />
        <DataSources />
        <WhoItsFor />
        <Differentiators />
        <OpenSource />
        <Roadmap />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
