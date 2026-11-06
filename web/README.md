# Cadrisyn web workspace

This is the first Next.js market workspace. Cadrisyn is a temporary working name.
The browser uses the same-origin `/api/v1/` routes; Next rewrites those requests to
the fixed `DJANGO_API_URL` server origin. The browser never chooses an API host.

## Local run

1. Start the Django API using the repository's implementation instructions and a
   development user.
2. Copy `.env.example` to `.env.local` if the API is not at
   `http://127.0.0.1:8000`. `DJANGO_API_URL` must contain only the server origin.
3. Run `npm ci`, then `npm run dev`.
4. Open `http://127.0.0.1:3000` and sign in with the development account.

The market workspace starts in Demo mode and labels synthetic bars beside the
chart and in the source inspector. Market mode is available only when the
authenticated session advertises it. A market-data error remains an error; it
never changes to demo data automatically.

## Checks

Set `PLAYWRIGHT_PRODUCTION=1` after a build to make browser acceptance start
the standalone server itself. This mode refuses to reuse a running server,
so a development process cannot be mistaken for the production build.

- `npm run lint`
- `npm run typecheck`
- `npm test`
- `npm run build`
- `npm run typegen` after the API owner has generated `../contracts/openapi.json`
- `npm run test:e2e` with the Django API running and an isolated development
  account in the ignored `.local/credentials.json` file

The end-to-end test signs in through the real same-origin API and exercises
instrument search, daily bars, range changes, watchlist persistence, and both
themes. It fails clearly when the local API or dedicated test credentials are
unavailable; it does not skip the user path.

Vitest 5.1 and Vite 7 use the project's Node 22.12+ runtime. The minimatch
override pins the upstream security fix used by the lint dependency tree.
Run the unit tests and lint before changing these pins. The initial and final
dependency audits are retained under `docs/implementation/evidence/`.

ESLint 9.39.5 remains pinned because the Next 16.4.5 preset includes React,
import, and accessibility plugins whose peer ranges exclude ESLint 10.
A trial of ESLint 10 produced an invalid dependency tree and was reverted.
ESLint 9 reports an upstream support warning. Upgrade the preset and its
plugins together before moving to ESLint 10; do not suppress peer conflicts.

Playwright's default browser cache works with `npx playwright install chromium`.
To keep downloads inside this repository, set `PLAYWRIGHT_BROWSERS_PATH` to
the absolute `.local/browsers` path for both installation and test commands.

For a local production-mode check, run `npm run build`, then `npm start` with
the Django API running. The starter copies static files and public notices
into the standalone build and binds to loopback by default. `HOSTNAME` and
`PORT` override the listener. This starts local processes; it does not deploy.
