import { Toaster as SonnerToaster } from "sonner";

export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: "oklch(0.14 0.008 155)",
          border: "1px solid oklch(0.22 0.01 155)",
          color: "oklch(0.93 0.005 155)",
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
        },
      }}
    />
  );
}
