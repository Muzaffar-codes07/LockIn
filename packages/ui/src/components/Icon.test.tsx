import { render } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { Icon } from "./Icon.js";

describe("Icon", () => {
  test("decorative icon (no label) gets aria-hidden and no role", () => {
    const { container } = render(
      <Icon>
        <path d="M0 0h24v24H0z" />
      </Icon>,
    );
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
    expect(svg?.getAttribute("role")).toBeNull();
  });

  test("labeled icon has role=img and aria-label", () => {
    const { container } = render(
      <Icon label="Search">
        <path d="M0 0h24v24H0z" />
      </Icon>,
    );
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("role")).toBe("img");
    expect(svg?.getAttribute("aria-label")).toBe("Search");
    expect(svg?.getAttribute("aria-hidden")).toBeNull();
  });

  test("size prop sets width and height", () => {
    const { container } = render(
      <Icon size={32}>
        <path d="M0 0h24v24H0z" />
      </Icon>,
    );
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("width")).toBe("32");
    expect(svg?.getAttribute("height")).toBe("32");
  });
});
