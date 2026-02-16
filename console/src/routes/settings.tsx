import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Key, User, CreditCard } from "lucide-react";
import { BYOKSettings } from "@/features/investigation/components/BYOKSettings";
import { useAuth } from "@/shared/hooks/use-auth";
import { useCredits } from "@/features/investigation/hooks/use-credits";
import { cn } from "@/shared/lib/utils";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";

export const Route = createFileRoute("/settings")({
    component: SettingsPage,
});

type SettingsTab = "profile" | "api";

function SettingsPage() {
    const [activeTab, setActiveTab] = useState<SettingsTab>("api");

    return (
        <div className="container mx-auto max-w-6xl p-6 md:p-10 space-y-8">
            <div className="space-y-1">
                <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
                <p className="text-muted-foreground text-lg">
                    Manage your account and preferences.
                </p>
            </div>

            <div className="h-px bg-border my-6" />

            <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] gap-8 lg:gap-12 items-start">
                {/* Navigation Sidebar */}
                <aside className="w-full relative">
                    <nav className="flex flex-row md:flex-col space-x-2 md:space-x-0 md:space-y-2 overflow-x-auto pb-4 md:pb-0 md:pr-8 md:border-r border-border">
                        <Button
                            variant={activeTab === "profile" ? "secondary" : "ghost"}
                            className={cn(
                                "justify-start text-left w-full",
                                activeTab === "profile" && "bg-secondary font-medium text-foreground"
                            )}
                            onClick={() => setActiveTab("profile")}
                        >
                            <User className="mr-2 h-4 w-4" />
                            Profile
                        </Button>
                        <Button
                            variant={activeTab === "api" ? "secondary" : "ghost"}
                            className={cn(
                                "justify-start text-left w-full",
                                activeTab === "api" && "bg-secondary font-medium text-foreground"
                            )}
                            onClick={() => setActiveTab("api")}
                        >
                            <Key className="mr-2 h-4 w-4" />
                            API Keys
                        </Button>
                    </nav>
                </aside>

                {/* Main Content Area */}
                <div className="w-full min-w-0 space-y-6">
                    {activeTab === "profile" && <ProfileSettings />}
                    {activeTab === "api" && <ApiSettings />}
                </div>
            </div>
        </div>
    );
}

function ProfileSettings() {
    const { user } = useAuth();
    const { data: creditData } = useCredits();

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
                <h3 className="text-lg font-medium">Profile</h3>
                <p className="text-sm text-muted-foreground">
                    Your personal account information.
                </p>
            </div>
            <div className="h-px bg-border" />

            <div className="grid gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-base">User Information</CardTitle>
                        <CardDescription>
                            Details about your currently signed-in account.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Email Address
                            </label>
                            <div className="flex rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm opacity-50 cursor-not-allowed bg-muted/50">
                                {user?.email}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <CreditCard className="h-5 w-5 text-primary" />
                            <CardTitle className="text-base">Credits & Usage</CardTitle>
                        </div>
                        <CardDescription>
                            Your current credit balance and plan status.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-lg border p-4 bg-card/50">
                            <div className="space-y-1">
                                <span className="font-semibold text-foreground">
                                    {creditData?.is_byok ? "BYOK Active" : "Standard Credits"}
                                </span>
                                <p className="text-xs text-muted-foreground max-w-[300px]">
                                    {creditData?.is_byok
                                        ? "You are using your own API key. No credits are consumed."
                                        : "Credits allow you to run investigations without an API key."}
                                </p>
                            </div>
                            <div className="mt-4 sm:mt-0 text-3xl font-bold tabular-nums">
                                {creditData?.credits ?? 0}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

function ApiSettings() {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
                <h3 className="text-lg font-medium">API Configuration</h3>
                <p className="text-sm text-muted-foreground">
                    Manage your API connection settings.
                </p>
            </div>
            <div className="h-px bg-border" />

            <div className="grid gap-6">
                <Card>
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Key className="h-5 w-5 text-primary" />
                            <CardTitle className="text-base">Anthropic API Key</CardTitle>
                        </div>
                        <CardDescription>
                            Configure your own API keys to bypass platform rate limits.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <BYOKSettings />
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
