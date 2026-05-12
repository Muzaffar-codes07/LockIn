import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { Stack } from "./Stack.js";

describe("Stack", () => {
  test("defaults to flex-col with gap-4", () => {
    render(<Stack data-testid="s">x</Stack>);
    const el = screen.getByTestId("s");
    expect(el.className).toContain("flex-col");
    expect(el.className).toContain("gap-4");
  });

  test("direction=row swaps to flex-row", () => {
    render(
      <Stack data-testid="s" direction="row" gap={8}>
        x
      </Stack>,
    );
    const el = screen.getByTestId("s");
    expect(el.className).toContain("flex-row");
    expect(el.className).toContain("gap-8");
  });

  test("align and justify map to Tailwind classes", () => {
    render(
      <Stack data-testid="s" align="center" justify="between">
        x
      </Stack>,
    );
    const el = screen.getByTestId("s");
    expect(el.className).toContain("items-center");
    expect(el.className).toContain("justify-between");
  });
});
