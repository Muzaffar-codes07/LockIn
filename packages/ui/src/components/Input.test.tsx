import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { Input } from "./Input.js";

describe("Input", () => {
  test("renders with placeholder", () => {
    render(<Input placeholder="Search" />);
    expect(screen.getByPlaceholderText("Search")).toBeInTheDocument();
  });

  test("invalid prop sets aria-invalid and danger border", () => {
    render(<Input invalid placeholder="bad" />);
    const input = screen.getByPlaceholderText("bad");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input.className).toContain("border-danger");
  });

  test("no invalid prop omits aria-invalid", () => {
    render(<Input placeholder="ok" />);
    expect(screen.getByPlaceholderText("ok")).not.toHaveAttribute("aria-invalid");
  });
});
