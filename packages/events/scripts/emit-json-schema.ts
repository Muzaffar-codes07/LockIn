import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { zodToJsonSchema } from "zod-to-json-schema";
import { EVENT_SCHEMAS } from "../src/schema.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(__dirname, "../dist/json-schema");
mkdirSync(outDir, { recursive: true });

const className = (eventType: string): string =>
  eventType
    .split(".")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");

// Write one schema per event type — for documentation and per-event consumers.
const perEvent: Record<string, unknown> = {};
for (const [eventType, schema] of Object.entries(EVENT_SCHEMAS)) {
  const json = zodToJsonSchema(schema, { name: className(eventType), $refStrategy: "none" });
  const fileName = eventType.replace(/\./g, "_") + ".json";
  writeFileSync(resolve(outDir, fileName), JSON.stringify(json, null, 2) + "\n");
  perEvent[className(eventType)] = (json as { definitions?: Record<string, unknown> }).definitions?.[
    className(eventType)
  ] ?? json;
  // eslint-disable-next-line no-console
  console.log(`wrote ${fileName} (${className(eventType)})`);
}

// Write the merged schema — datamodel-codegen consumes this single file so the
// generated Python lives in one `generated.py` module instead of a sub-package.
const merged = {
  $schema: "http://json-schema.org/draft-07/schema#",
  title: "LockInEvents",
  type: "object",
  description: "All LockIn v1 event types as JSON Schema definitions.",
  definitions: perEvent,
};
writeFileSync(resolve(outDir, "_all.json"), JSON.stringify(merged, null, 2) + "\n");
// eslint-disable-next-line no-console
console.log("wrote _all.json (merged)");
