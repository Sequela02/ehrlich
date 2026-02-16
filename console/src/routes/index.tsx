import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { LogIn, Sparkles } from "lucide-react";
import { PromptInput, TemplateCards } from "@/features/investigation/components";
import { useAuth } from "@/shared/hooks/use-auth";
import { Button } from "@/shared/components/ui/button";
import { InteractiveLogo } from "@/shared/components/InteractiveLogo";
import { GREETINGS } from "@/shared/lib/constants";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { user, isLoading: authLoading, signIn } = useAuth();
  const [prompt, setPrompt] = useState("");
  const [greeting, setGreeting] = useState(GREETINGS[0]);

  useEffect(() => {
    setGreeting(GREETINGS[Math.floor(Math.random() * GREETINGS.length)]);
  }, []);

  return (
    <div className="flex h-full flex-col items-center justify-center p-8">
      <div className="flex w-full max-w-2xl flex-col gap-12">
        {/* Hero */}
        <div className="flex flex-col items-center gap-6 text-center">
          <InteractiveLogo />
          <h1 className="text-2xl font-medium tracking-tight text-foreground/80">
            {greeting}
          </h1>
        </div>

        {/* Prompt or Sign-in */}
        {!authLoading && !user ? (
          <Card className="mx-auto w-full max-w-md shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader className="text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-muted/50">
                <LogIn className="h-6 w-6 text-muted-foreground" />
              </div>
              <CardTitle>Sign in required</CardTitle>
              <CardDescription>
                Use your account to run AI-powered scientific investigations
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center pb-8">
              <Button onClick={() => signIn()} size="lg" className="w-full sm:w-auto px-8">
                Sign in
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <PromptInput value={prompt} onChange={setPrompt} />

            {/* Research Templates - Subtle */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground/50">
                <Sparkles className="h-3 w-3" />
                <span>Suggested Templates</span>
              </div>
              <TemplateCards onSelect={setPrompt} limit={3} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
