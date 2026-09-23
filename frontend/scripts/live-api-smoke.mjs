import { createServer } from "vite";

function readApiOrigin(args) {
  const option = args.indexOf("--api-base");
  const raw = option === -1 ? process.env.API_BASE_URL ?? "http://127.0.0.1:8000" : args[option + 1];
  if (!raw) {
    throw new Error("--api-base requires an HTTP(S) origin.");
  }

  const url = new URL(raw);
  if ((url.protocol !== "http:" && url.protocol !== "https:") || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("API base must be an HTTP(S) origin without a path, query, or fragment.");
  }
  return url.origin;
}

const apiOrigin = readApiOrigin(process.argv.slice(2));
process.env.VITE_USE_MOCKS = "false";
process.env.VITE_API_BASE_URL = apiOrigin;

// AnalystApiClient uses the browser timer API. Node 20+ provides the same timer
// functions; this makes the real frontend module executable without a browser.
globalThis.window ??= globalThis;

const vite = await createServer({
  root: process.cwd(),
  server: { middlewareMode: true },
  appType: "custom",
});

try {
  const origin = "http://127.0.0.1:5173";
  const cors = await fetch(`${apiOrigin}/api/v1/runs`, {
    method: "OPTIONS",
    headers: {
      Origin: origin,
      "Access-Control-Request-Method": "POST",
      "Access-Control-Request-Headers": "content-type",
    },
  });
  if (cors.status !== 200 || cors.headers.get("access-control-allow-origin") !== origin) {
    throw new Error("The API did not allow the frontend development origin through CORS.");
  }

  const frontend = await vite.ssrLoadModule("/src/config.ts");
  const config = frontend.readRuntimeConfig();
  if (config.useMocks || config.apiBaseUrl !== apiOrigin) {
    throw new Error(`Live frontend configuration was not applied: ${JSON.stringify(config)}`);
  }

  const client = frontend.createApiClient(config);
  const summary = await client.getCaseSummary();
  const statuses = [];
  const result = await client.createAndPoll(
    { seed: 42, mode: "mock" },
    { onSnapshot: (snapshot) => statuses.push(snapshot.status) },
  );

  if (summary.source !== "mock_environment" || result.status !== "completed" || statuses.length === 0) {
    throw new Error("The frontend client did not complete the API workflow.");
  }

  console.log(
    `PASS live frontend/API smoke: ${statuses.join(" -> ")}; `
      + `${result.n_pilots} pilots, ${result.n_campaigns} final campaigns.`,
  );
} finally {
  await vite.close();
}
