import { readFileSync, readdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, test } from "vitest";
import { EVENT_SCHEMAS, LockInEvent } from "../src/index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const fixturesDir = resolve(__dirname, "../fixtures");

describe("event schema fixtures", () => {
  const files = readdirSync(fixturesDir).filter((f) => f.endsWith(".json"));

  test("there is a fixture for every event type", () => {
    expect(new Set(files.map((f) => f.replace(/\.json$/, "")))).toEqual(
      new Set(Object.keys(EVENT_SCHEMAS)),
    );
  });

  for (const file of files) {
    const eventType = file.replace(/\.json$/, "") as keyof typeof EVENT_SCHEMAS;

    test(`${eventType} round-trips through Zod`, () => {
      const raw = JSON.parse(readFileSync(resolve(fixturesDir, file), "utf-8"));
      const parsed = EVENT_SCHEMAS[eventType].parse(raw);
      const reparsed = EVENT_SCHEMAS[eventType].parse(JSON.parse(JSON.stringify(parsed)));
      expect(reparsed).toEqual(parsed);
    });

    test(`${eventType} parses through the discriminated union`, () => {
      const raw = JSON.parse(readFileSync(resolve(fixturesDir, file), "utf-8"));
      const parsed = LockInEvent.parse(raw);
      expect(parsed.event_type).toBe(eventType);
    });
  }
});
