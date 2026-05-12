import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { Button } from "./Button.js";

describe("Button", () => {
  test("renders with default type=button", () => {
    render(<Button>Submit</Button>);
    const btn = screen.getByRole("button", { name: "Submit" });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveAttribute("type", "button");
  });

  test("respects type override", () => {
    render(<Button type="submit">Go</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("type", "submit");
  });

  test("disabled state blocks pointer", () => {
    render(<Button disabled>Off</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  test("applies variant + size classes", () => {
    render(
      <Button variant="danger" size="lg">
        Delete
      </Button>,
    );
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-danger");
    expect(btn.className).toContain("h-12");
  });
});
