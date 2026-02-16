import { useMutation } from "@tanstack/react-query";
import { apiUpload } from "@/shared/lib/api";
import type { UploadResponse } from "../types";

export function useUpload() {
  return useMutation({
    mutationFn: async (file: File): Promise<UploadResponse> => {
      const form = new FormData();
      form.append("file", file);
      return apiUpload<UploadResponse>("/upload", form);
    },
  });
}
