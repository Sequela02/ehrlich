import { lazy, Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";

const HowItWorks = lazy(() =>
  import("@/components/HowItWorks").then((m) => ({ default: m.HowItWorks })),
);
const ConsolePreview = lazy(() =>
  import("@/components/ConsolePreview").then((m) => ({
    default: m.ConsolePreview,
  })),
);
const Architecture = lazy(() =>
  import("@/components/Architecture").then((m) => ({
    default: m.Architecture,
  })),
);
const Domains = lazy(() =>
  import("@/components/Domains").then((m) => ({ default: m.Domains })),
);
const Visualizations = lazy(() =>
  import("@/components/Visualizations").then((m) => ({
    default: m.Visualizations,
  })),
);
const DataSources = lazy(() =>
  import("@/components/DataSources").then((m) => ({
    default: m.DataSources,
  })),
);
const WhoItsFor = lazy(() =>
  import("@/components/WhoItsFor").then((m) => ({ default: m.WhoItsFor })),
);
const Differentiators = lazy(() =>
  import("@/components/Differentiators").then((m) => ({
    default: m.Differentiators,
  })),
);
const OpenSource = lazy(() =>
  import("@/components/OpenSource").then((m) => ({ default: m.OpenSource })),
);
const Roadmap = lazy(() =>
  import("@/components/Roadmap").then((m) => ({ default: m.Roadmap })),
);
const CTA = lazy(() =>
  import("@/components/CTA").then((m) => ({ default: m.CTA })),
);
const Footer = lazy(() =>
  import("@/components/Footer").then((m) => ({ default: m.Footer })),
);

export const Route = createFileRoute("/")({
  component: LandingPage,
});

const SectionFallback = <div className="h-24" />;

function LandingPage() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Suspense fallback={SectionFallback}>
          <HowItWorks />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <ConsolePreview />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <Architecture />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <Domains />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <Visualizations />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <DataSources />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <WhoItsFor />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <Differentiators />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <OpenSource />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <Roadmap />
        </Suspense>
        <Suspense fallback={SectionFallback}>
          <CTA />
        </Suspense>
      </main>
      <Suspense fallback={SectionFallback}>
        <Footer />
      </Suspense>
    </>
  );
}
