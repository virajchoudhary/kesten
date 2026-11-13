import { cp, mkdir, access } from "node:fs/promises";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const standalone = join(root, ".next/standalone");
await access(join(standalone, "server.js"));
await mkdir(join(standalone, ".next"), { recursive: true });
await cp(join(root, ".next/static"), join(standalone, ".next/static"), { recursive: true });
await cp(join(root, "public"), join(standalone, "public"), { recursive: true });

const server = spawn(process.execPath, [join(standalone, "server.js")], {
  cwd: standalone,
  stdio: "inherit",
  env: { ...process.env, NODE_ENV: "production", HOSTNAME: process.env.HOSTNAME ?? "127.0.0.1", PORT: process.env.PORT ?? "3000" },
});
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => server.kill(signal));
server.on("error", (error) => { console.error(error.message); process.exitCode = 1; });
server.on("exit", (code) => { process.exitCode = code ?? 1; });
