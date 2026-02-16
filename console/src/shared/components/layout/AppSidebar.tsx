import { useState } from "react";
import logoUrl from "@/assets/images/logo.svg";
import { Link } from "@tanstack/react-router";
import {
    BookOpen,
    LogIn,
    LogOut,
    Plus,
    Search,
    Settings,
    X,
    PanelLeftClose,
    PanelLeftOpen,
} from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { useAuth } from "@/shared/hooks/use-auth";
import { useInvestigations } from "@/features/investigation/hooks/use-investigations";
import { useCredits } from "@/features/investigation/hooks/use-credits";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/shared/components/ui/tooltip";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

interface AppSidebarProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    collapsed: boolean;
    setCollapsed: (collapsed: boolean) => void;
    onMethodologyClick: () => void;
}

export function AppSidebar({
    open,
    setOpen,
    collapsed,
    setCollapsed,
    onMethodologyClick,
}: AppSidebarProps) {
    const { user, signIn, signOut } = useAuth();
    const { data: investigations } = useInvestigations();
    const { data: creditData } = useCredits();
    const [searchTerm, setSearchTerm] = useState("");

    const filteredInvestigations = investigations?.filter((inv) =>
        inv.prompt.toLowerCase().includes(searchTerm.toLowerCase()),
    );

    return (
        <TooltipProvider>
            {/* Mobile Overlay */}
            <div
                className={cn(
                    "fixed inset-0 z-40 bg-black/40 lg:hidden",
                    open ? "block" : "hidden",
                )}
                onClick={() => setOpen(false)}
            />

            {/* Sidebar */}
            <aside
                className={cn(
                    "fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-background transition-all duration-200 lg:static",
                    open ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
                    collapsed ? "w-16" : "w-72"
                )}
            >
                {/* Header */}
                <div className={cn(
                    "flex h-14 shrink-0 items-center border-b border-border transition-all",
                    collapsed ? "justify-center px-0" : "justify-between px-4"
                )}>
                    {!collapsed && (
                        <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
                            <img src={logoUrl} alt="Ehrlich Logo" className="h-8 w-auto" />
                            EHRLICH
                        </Link>
                    )}

                    {/* Desktop Toggle */}
                    <button
                        onClick={() => setCollapsed(!collapsed)}
                        className={cn(
                            "hidden rounded-md p-1 text-muted-foreground hover:bg-muted lg:flex",
                            collapsed && "h-10 w-10 items-center justify-center"
                        )}
                        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {collapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
                    </button>

                    {/* Mobile Close */}
                    <button
                        onClick={() => setOpen(false)}
                        className="rounded-md p-1 text-muted-foreground hover:bg-muted lg:hidden"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex flex-1 flex-col overflow-hidden">
                    {/* New Investigation Button */}
                    <div className={cn("p-4", collapsed && "flex justify-center px-2")}>
                        {collapsed ? (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Link
                                        to="/"
                                        className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground transition-colors hover:bg-primary/90"
                                    >
                                        <Plus className="h-5 w-5" />
                                    </Link>
                                </TooltipTrigger>
                                <TooltipContent side="right">
                                    New Investigation
                                </TooltipContent>
                            </Tooltip>
                        ) : (
                            <Link
                                to="/"
                                className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                                onClick={() => {
                                    if (window.innerWidth < 1024) setOpen(false);
                                }}
                            >
                                <Plus className="h-4 w-4" />
                                New Investigation
                            </Link>
                        )}
                    </div>

                    {/* Navigation / History */}
                    <div className="flex-1 overflow-y-auto px-2">
                        {!collapsed ? (
                            <>
                                <div className="mb-2 px-2 text-xs font-semibold text-muted-foreground/50">
                                    Recent Investigations
                                </div>

                                {/* Search */}
                                <div className="mb-2 px-2">
                                    <div className="relative">
                                        <Search className="absolute left-2 top-1.5 h-3.5 w-3.5 text-muted-foreground" />
                                        <input
                                            type="text"
                                            placeholder="Filter..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            className="w-full rounded-sm border border-border bg-muted/40 py-1 pl-7 pr-2 text-xs focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-0.5">
                                    {filteredInvestigations?.map((inv) => (
                                        <Link
                                            key={inv.id}
                                            to="/investigation/$id"
                                            params={{ id: inv.id }}
                                            className="group flex flex-col gap-0.5 rounded-md px-2 py-2 transition-colors hover:bg-muted/50"
                                            activeProps={{ className: "bg-muted text-foreground" }}
                                            onClick={() => {
                                                if (window.innerWidth < 1024) setOpen(false);
                                            }}
                                        >
                                            <div className="flex items-center justify-between gap-2">
                                                <span className="truncate text-xs font-medium text-foreground/80 group-hover:text-foreground">
                                                    {inv.prompt}
                                                </span>
                                                {inv.status === "running" && (
                                                    <span className="flex h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-primary" />
                                                )}
                                                {inv.status === "awaiting_approval" && (
                                                    <span className="flex h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-accent" />
                                                )}
                                                {inv.status === "cancelled" && (
                                                    <span className="flex h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/40" />
                                                )}
                                            </div>
                                            <span className="truncate text-[10px] text-muted-foreground/60">
                                                {new Date(inv.created_at).toLocaleDateString()}
                                            </span>
                                        </Link>
                                    ))}

                                    {investigations?.length === 0 && (
                                        <div className="px-2 py-8 text-center text-xs text-muted-foreground/50">
                                            No history yet
                                        </div>
                                    )}
                                </div>
                            </>
                        ) : (
                            /* Collapsed History Icons (Optional: show last few?) */
                            <div className="flex flex-col items-center gap-2 pt-2">
                                <div className="h-px w-8 bg-border" />
                            </div>
                        )}
                    </div>

                    {/* Footer Nav Integration */}
                    <div className="mt-auto border-t border-border bg-background p-2">
                        {/* Methodology Link - Always Accessible */}
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <button
                                    onClick={onMethodologyClick}
                                    className={cn(
                                        "flex w-full items-center gap-2 rounded-md py-2 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors",
                                        collapsed ? "justify-center" : "px-2"
                                    )}
                                >
                                    <BookOpen className="h-4 w-4 shrink-0" />
                                    {!collapsed && <span>Methodology</span>}
                                </button>
                            </TooltipTrigger>
                            {collapsed && <TooltipContent side="right">Methodology</TooltipContent>}
                        </Tooltip>
                    </div>


                    {/* User Footer with DropdownMenu */}
                    <div className={cn("border-t border-border", collapsed ? "p-2" : "p-3")}>
                        {!user ? (
                            collapsed ? (
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <button
                                            onClick={() => signIn()}
                                            className="flex h-10 w-full items-center justify-center rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
                                        >
                                            <LogIn className="h-4 w-4" />
                                        </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="right">
                                        Sign In
                                    </TooltipContent>
                                </Tooltip>
                            ) : (
                                <button
                                    onClick={() => signIn()}
                                    className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                                >
                                    <LogIn className="h-4 w-4" />
                                    Sign In
                                </button>
                            )
                        ) : (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <button className={cn(
                                        "flex items-center gap-2 w-full rounded-md hover:bg-muted transition-colors outline-none h-9",
                                        collapsed ? "justify-center p-0" : "px-2"
                                    )}>
                                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-primary/10 text-[10px] font-medium text-primary">
                                            {user?.email?.charAt(0).toUpperCase()}
                                        </div>

                                        {!collapsed && (
                                            <>
                                                <div className="flex min-w-0 flex-1 flex-col items-start px-1 text-left">
                                                    <span className="w-full truncate text-xs font-medium text-foreground">
                                                        {user.email}
                                                    </span>
                                                    <span className="flex items-center gap-1.5 truncate text-[10px] text-muted-foreground/70">
                                                        {creditData?.credits ?? 0} credits
                                                    </span>
                                                </div>
                                                <Settings className="h-3.5 w-3.5 text-muted-foreground/50" />
                                            </>
                                        )}
                                    </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent side={collapsed ? "right" : "top"} align={collapsed ? "end" : "start"} className="w-56" sideOffset={8}>
                                    <DropdownMenuLabel>
                                        <div className="flex flex-col space-y-1">
                                            <p className="text-sm font-medium leading-none">{user.email}</p>
                                            <p className="text-xs leading-none text-muted-foreground">
                                                {creditData?.is_byok ? "BYOK Plan" : "Standard Plan"}
                                            </p>
                                        </div>
                                    </DropdownMenuLabel>
                                    <DropdownMenuSeparator />
                                    <Link to="/settings" className="w-full">
                                        <DropdownMenuItem className="cursor-pointer">
                                            <Settings className="mr-2 h-4 w-4" />
                                            <span>Settings & API keys</span>
                                        </DropdownMenuItem>
                                    </Link>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={() => signOut()} className="text-destructive focus:text-destructive cursor-pointer">
                                        <LogOut className="mr-2 h-4 w-4" />
                                        <span>Sign out</span>
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        )}
                    </div>
                </div>
            </aside>
        </TooltipProvider>
    );
}
