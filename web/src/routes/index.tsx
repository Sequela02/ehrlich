import { createFileRoute } from "@tanstack/react-router";
import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { Architecture } from "@/components/Architecture";
import { Domains } from "@/components/Domains";
import { DataSources } from "@/components/DataSources";
import { OpenSource } from "@/components/OpenSource";
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
        <Architecture />
        <Domains />
        <DataSources />
        <OpenSource />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
