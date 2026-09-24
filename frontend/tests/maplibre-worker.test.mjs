// Run against `next start` or `next dev`:
// MAP_TEST_ORIGIN=http://127.0.0.1:3100 node --experimental-vm-modules tests/maplibre-worker.test.mjs
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, basename } from "node:path";
import { test } from "node:test";
import { SourceTextModule } from "node:vm";

const require = createRequire(import.meta.url);
const packagePath = require.resolve("maplibre-gl/package.json");
const { version } = require(packagePath);
const origin = process.env.MAP_TEST_ORIGIN ?? "http://127.0.0.1:3100";

test("MapLibre worker and every module dependency are served as matching JavaScript", async () => {
  const visited = new Set();
  async function load(url) {
    assert.equal(new URL(url).origin, new URL(origin).origin);
    const response = await fetch(url);
    assert.equal(response.status, 200, url);
    assert.match(response.headers.get("content-type") ?? "", /(?:java|ecma)script/i, url);
    const source = await response.text();
    assert.equal(source, await readFile(join(dirname(packagePath), "dist", basename(url)), "utf8"));
    visited.add(url);
    return new SourceTextModule(source, { identifier: url });
  }
  const worker = await load(`${origin}/maplibre/${version}/maplibre-gl-worker.mjs`);
  await worker.link((specifier, parent) => load(new URL(specifier, parent.identifier).href));
  assert.equal(worker.status, "linked");
  assert.ok(visited.has(`${origin}/maplibre/${version}/maplibre-gl-shared.mjs`));
});
