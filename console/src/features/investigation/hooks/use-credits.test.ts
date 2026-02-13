import { describe, it, expect } from "vitest";
import { useCredits } from "./use-credits";

describe("useCredits", () => {
  it("is a function", () => {
    expect(typeof useCredits).toBe("function");
  });
});
