import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { Card } from "./Card.js";

describe("Card", () => {
  test("renders children inside a div with card classes", () => {
    render(
      <Card data-testid="c">
        <p>hello</p>
      </Card>,
    );
    const card = screen.getByTestId("c");
    expect(card.tagName).toBe("DIV");
    expect(card.className).toContain("rounded-lg");
    expect(screen.getByText("hello")).toBeInTheDocument();
  });
});
