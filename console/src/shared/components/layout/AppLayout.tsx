import { useState, createContext, useContext, useEffect, type ReactNode } from "react";
import { Menu } from "lucide-react";
import { useLocation } from "@tanstack/react-router";
import { Toaster } from "@/shared/components/ui/Toaster";
import { MethodologyDrawer } from "./MethodologyDrawer";
import { AppSidebar } from "./AppSidebar";

interface LayoutContextType {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined);

export function useLayout() {
  const context = useContext(LayoutContext);
  if (!context) {
    throw new Error("useLayout must be used within AppLayout");
  }
  return context;
}

interface AppLayoutProps {
  children: ReactNode;
  hideHeader?: boolean;
}

export function AppLayout({ children, hideHeader }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    // Persist collapsed state
    if (typeof window !== "undefined") {
      return localStorage.getItem("sidebarCollapsed") === "true";
    }
    return false;
  });
  const [methodologyOpen, setMethodologyOpen] = useState(false);
  const location = useLocation();

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  // Update persistence
  useEffect(() => {
    localStorage.setItem("sidebarCollapsed", String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  return (
    <LayoutContext.Provider
      value={{
        sidebarOpen,
        setSidebarOpen,
        sidebarCollapsed,
        setSidebarCollapsed,
      }}
    >
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <AppSidebar
          open={sidebarOpen}
          setOpen={setSidebarOpen}
          collapsed={sidebarCollapsed}
          setCollapsed={setSidebarCollapsed}
          onMethodologyClick={() => setMethodologyOpen(true)}
        />

        <main className="flex flex-1 flex-col overflow-hidden bg-background transition-all duration-200 ease-in-out">
          {/* Mobile Header for generic pages */}
          {!hideHeader && (
            <header className="flex h-14 shrink-0 items-center border-b border-border px-4 lg:hidden">
              <button
                onClick={() => setSidebarOpen(true)}
                className="mr-3 rounded-md p-1 text-muted-foreground hover:bg-muted"
                aria-label="Open sidebar"
              >
                <Menu className="h-5 w-5" />
              </button>
              <span className="font-semibold tracking-tight">EHRLICH</span>
            </header>
          )}

          {/* Page Content */}
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
        </main>

        <Toaster />
        <MethodologyDrawer
          open={methodologyOpen}
          onClose={() => setMethodologyOpen(false)}
        />
      </div>
    </LayoutContext.Provider>
  );
}
