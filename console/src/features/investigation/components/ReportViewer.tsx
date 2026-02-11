import Markdown from "react-markdown";

interface ReportViewerProps {
  content: string;
}

export function ReportViewer({ content }: ReportViewerProps) {
  if (!content) {
    return (
      <p className="text-sm text-muted-foreground">
        Report will appear after investigation completes.
      </p>
    );
  }

  return (
    <div className="prose prose-sm prose-invert max-w-none prose-headings:text-foreground prose-a:text-primary prose-strong:text-foreground prose-code:text-primary prose-pre:rounded-lg prose-pre:border prose-pre:border-border prose-pre:bg-muted">
      <Markdown>{content}</Markdown>
    </div>
  );
}
