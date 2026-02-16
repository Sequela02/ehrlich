/// <reference types="vite/client" />
import {
  createRootRoute,
  HeadContent,
  Outlet,
  Scripts,
} from "@tanstack/react-router";
import type { ReactNode } from "react";
import appCss from "@/styles/app.css?url";

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Ehrlich — Scientific Methodology, Automated" },
      {
        name: "description",
        content:
          "Formulate hypotheses, design experiments, test against 19 real databases, grade evidence. 85 computational tools across 4 scientific domains. Open source (AGPL-3.0), self-hostable.",
      },
      { name: "theme-color", content: "#1a2a1a" },
      { property: "og:title", content: "Ehrlich — Scientific Methodology, Automated" },
      {
        property: "og:description",
        content:
          "85 computational tools. 19 data sources. 4 scientific domains. Hypothesis-driven reasoning grounded in Popper, Fisher, and GRADE. Open source, self-hostable.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/logo.svg", type: "image/svg+xml" },
      {
        rel: "preload",
        href: "/fonts/space-grotesk-400.woff2",
        as: "font",
        type: "font/woff2",
        crossOrigin: "anonymous",
      },
      {
        rel: "preload",
        href: "/fonts/jetbrains-mono-400.woff2",
        as: "font",
        type: "font/woff2",
        crossOrigin: "anonymous",
      },
    ],
  }),
  shellComponent: RootDocument,
});

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body className="font-sans antialiased">
        <Outlet />
        <Scripts />
      </body>
    </html>
  );
}
