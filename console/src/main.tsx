import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { AuthKitProvider } from "@workos-inc/authkit-react";
import { useAuth } from "@/shared/hooks/use-auth";
import { setTokenProvider } from "@/shared/lib/api";
import { routeTree } from "./routeTree.gen";
import "./styles/globals.css";
import "./styles/print.css";

const WORKOS_CLIENT_ID = import.meta.env.VITE_WORKOS_CLIENT_ID;
const WORKOS_REDIRECT_URI = import.meta.env.VITE_WORKOS_REDIRECT_URI;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

/** Syncs WorkOS getAccessToken into the module-level API fetch wrapper. */
function AuthSync({ children }: { children: React.ReactNode }) {
  const { getAccessToken } = useAuth();

  useEffect(() => {
    setTokenProvider(getAccessToken);
  }, [getAccessToken]);

  return <>{children}</>;
}

/** Wraps children in AuthKitProvider when WorkOS is configured, passes through otherwise. */
function AuthWrapper({ children }: { children: React.ReactNode }) {
  if (!WORKOS_CLIENT_ID) return <>{children}</>;

  return (
    <AuthKitProvider clientId={WORKOS_CLIENT_ID} redirectUri={WORKOS_REDIRECT_URI} devMode={import.meta.env.DEV}>
      <AuthSync>{children}</AuthSync>
    </AuthKitProvider>
  );
}

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Root element not found");

createRoot(rootElement).render(
  <StrictMode>
    <AuthWrapper>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </AuthWrapper>
  </StrictMode>,
);
