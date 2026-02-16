import { createRootRoute, Outlet, useMatches } from "@tanstack/react-router";
import { AppLayout } from "@/shared/components/layout/AppLayout";

const HEADERLESS_ROUTES = ["/investigation/", "/compare/", "/paper/"];

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  const matches = useMatches();
  const pathname = matches[matches.length - 1]?.pathname ?? "";
  const hideHeader = HEADERLESS_ROUTES.some((r) => pathname.startsWith(r));

  return (
    <AppLayout hideHeader={hideHeader}>
      <Outlet />
    </AppLayout>
  );
}
