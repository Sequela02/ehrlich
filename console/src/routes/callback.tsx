import { createFileRoute, Navigate } from "@tanstack/react-router";
import { useAuth } from "@/shared/hooks/use-auth";

export const Route = createFileRoute("/callback")({
  component: CallbackPage,
});

/**
 * AuthKitProvider intercepts the ?code= param and exchanges it for tokens.
 * Wait until auth finishes loading, then redirect home.
 */
function CallbackPage() {
  const { isLoading } = useAuth();

  if (isLoading) return null;

  return <Navigate to="/" />;
}
