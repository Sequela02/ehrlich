import { ArrowLeft, Menu } from "lucide-react";
import { Link, useRouter } from "@tanstack/react-router";
import { useLayout } from "./AppLayout";
import { cn } from "@/shared/lib/utils";

interface PageHeaderProps {
    title: string;
    titleMaxLength?: number;
    subtitle?: string;
    backTo?: string;
    rightContent?: React.ReactNode;
    className?: string;
}

export function PageHeader({
    title,
    titleMaxLength,
    subtitle,
    backTo,
    rightContent,
    className,
}: PageHeaderProps) {
    const isTruncated = titleMaxLength && title.length > titleMaxLength;
    const displayTitle = isTruncated ? title.slice(0, titleMaxLength).trimEnd() + "..." : title;
    const router = useRouter();
    const { setSidebarOpen } = useLayout();

    return (
        <header
            className={cn(
                "shrink-0 border-b border-border bg-background px-4 py-3 lg:px-6",
                className,
            )}
        >
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 overflow-hidden">
                    {/* Mobile Sidebar Toggle */}
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="rounded-md p-1 text-muted-foreground hover:bg-muted lg:hidden"
                        aria-label="Open sidebar"
                    >
                        <Menu className="h-5 w-5" />
                    </button>

                    {/* Back Button */}
                    {backTo ? (
                        <Link
                            to={backTo}
                            className="hidden rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground lg:inline-flex"
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </Link>
                    ) : (
                        <button
                            onClick={() => router.history.back()}
                            className="hidden rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground lg:inline-flex"
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </button>
                    )}

                    <div className="min-w-0">
                        <h1
                            className="truncate text-lg font-semibold lg:text-xl"
                            title={isTruncated ? title : undefined}
                        >
                            {displayTitle}
                        </h1>
                        {subtitle && (
                            <p className="truncate font-mono text-[11px] text-muted-foreground">
                                {subtitle}
                            </p>
                        )}
                    </div>
                </div>

                {rightContent && (
                    <div className="flex shrink-0 items-center gap-3">
                        {rightContent}
                    </div>
                )}
            </div>
        </header>
    );
}
