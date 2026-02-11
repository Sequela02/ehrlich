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
          currentItemFontFamily: 2,
          currentItemStrokeColor: "#1e1e1e",
        },
      }}
      viewModeEnabled={viewMode}
      theme={THEME.DARK}
      UIOptions={{
        canvasActions: {
          toggleTheme: false,
          export: false,
        },
      }}
    />
  );
}
