import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { CommandPalette } from "./command-palette";

describe("CommandPalette", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <CommandPalette open={false} onOpenChange={() => {}} onSubmit={() => {}} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("submits the trimmed title and closes on Enter", () => {
    const onSubmit = vi.fn();
    const onOpenChange = vi.fn();
    render(<CommandPalette open onOpenChange={onOpenChange} onSubmit={onSubmit} />);

    const input = screen.getByPlaceholderText("What needs doing?");
    fireEvent.change(input, { target: { value: "  Write the spec  " } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onSubmit).toHaveBeenCalledWith("Write the spec");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("ignores a blank title", () => {
    const onSubmit = vi.fn();
    render(<CommandPalette open onOpenChange={() => {}} onSubmit={onSubmit} />);

    const input = screen.getByPlaceholderText("What needs doing?");
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onSubmit).not.toHaveBeenCalled();
  });
});
