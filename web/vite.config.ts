import { defineConfig } from "vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";
import tsConfigPaths from "vite-tsconfig-paths";
import tailwindcss from "@tailwindcss/vite";
import { nitro } from "nitro/vite";

export default defineConfig({
  server: {
    port: 3000,
    host: true,
    allowedHosts: [
      "gruesomely-euplastic-lashon.ngrok-free.dev",
    ],
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
  },
  plugins: [
    tailwindcss(),
    tsConfigPaths({ projects: ["./tsconfig.json"] }),
    tanstackStart({ srcDirectory: "src" }),
    viteReact(),
    nitro(),
  ],
  build: {
    chunkSizeWarningLimit: 300,
  },
});
