declare module "3dmol" {
  interface ViewerSpec {
    backgroundColor?: string;
  }

  interface AtomSelectionSpec {
    model?: number;
  }

  interface AtomStyleSpec {
    stick?: { colorscheme?: string };
    cartoon?: { color?: string };
  }

  interface GLViewer {
    addModel(data: string, format: string): GLModel;
    setStyle(sel: AtomSelectionSpec, style: AtomStyleSpec): void;
    zoomTo(sel?: AtomSelectionSpec): void;
    render(): void;
    clear(): void;
    removeAllModels(): void;
  }

  interface GLModel {}

  function createViewer(
    element: HTMLElement,
    spec?: ViewerSpec,
  ): GLViewer;
}
