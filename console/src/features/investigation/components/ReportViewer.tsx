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
    <div className="prose prose-sm max-w-none">
      <Markdown>{content}</Markdown>
    </div>
  );
}
