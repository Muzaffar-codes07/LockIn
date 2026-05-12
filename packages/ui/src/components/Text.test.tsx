import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { Text } from "./Text.js";

describe("Text", () => {
  test("renders as <p> by default", () => {
    render(<Text>hi</Text>);
    expect(screen.getByText("hi").tagName).toBe("P");
  });

  test("as prop swaps element", () => {
    render(
      <Text as="h1" size="2xl">
        Title
      </Text>,
    );
    const el = screen.getByText("Title");
    expect(el.tagName).toBe("H1");
    expect(el.className).toContain("text-2xl");
  });

  test("tone=muted applies muted color class", () => {
    render(<Text tone="muted">faded</Text>);
    expect(screen.getByText("faded").className).toContain("text-text-muted");
  });

  test("weight maps to font-* class", () => {
    render(<Text weight="bold">strong</Text>);
    expect(screen.getByText("strong").className).toContain("font-bold");
  });
});
