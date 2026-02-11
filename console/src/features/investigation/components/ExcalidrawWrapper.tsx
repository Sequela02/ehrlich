import { useMemo } from "react";
import { Excalidraw, convertToExcalidrawElements, THEME } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import type { ExcalidrawElementSkeleton } from "@excalidraw/excalidraw/data/transform";

interface ExcalidrawWrapperProps {
  skeletons: ExcalidrawElementSkeleton[];
  viewMode: boolean;
}

export default function ExcalidrawWrapper({ skeletons, viewMode }: ExcalidrawWrapperProps) {
  const elements = useMemo(
    () => convertToExcalidrawElements(skeletons, { regenerateIds: false }),
    [skeletons],
  );

  return (
    <Excalidraw
      initialData={{
        elements,
        scrollToContent: true,
        appState: {
          theme: THEME.DARK,
          viewBackgroundColor: "#0f1219",
        },
      }}
      viewModeEnabled={viewMode}
      theme={THEME.DARK}
    />
  );
}
