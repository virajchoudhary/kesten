# Run and verify Cadrisyn

## Local development

Run `scripts/setup.ps1` on Windows or `sh scripts/setup.sh` on Linux with Python 3.12 and Node 22 LTS installed. Run `.venv/Scripts/python.exe scripts/dev.py` on Windows or `.venv/bin/python scripts/dev.py` on Linux. The launcher migrates only `.local/cadrisyn.sqlite3`, bootstraps a local analyst, and starts Django on `127.0.0.1:8000` and Next.js on `127.0.0.1:3000`.

`--api-only` starts Django for browser tests. A failure in either owned child stops the other. The launcher never starts Redis, Celery, training, or a cloud service. Market mode is off unless explicitly enabled. Password files, secrets, databases, caches, generated reports, and environments remain ignored.

Use separate shells for the API and browser test runner. The test runner must use the same local API and credential file. Do not point it at a shared or production account.

## Container preview

`compose.yaml` is a local HTTP preview configuration. It binds the gateway only to `127.0.0.1:8080`. PostgreSQL and Redis have no host ports. The API and web images run as non-root users. Docker execution and PostgreSQL migration must be verified on a host with Docker before this configuration is accepted.

Copy `config/.env.example` to an ignored environment file. Replace the example secrets. Use a URL-safe database password because Compose interpolates it into `DATABASE_URL`. Do not reuse a development secret in production.

```sh
docker compose --env-file .env.preview build
docker compose --env-file .env.preview run --rm api python manage.py migrate --noinput
docker compose --env-file .env.preview run --rm api python manage.py createsuperuser
docker compose --env-file .env.preview up
```

Open `http://127.0.0.1:8080`. Sign in with the account created above. This manual account step avoids shipping a shared administrator password. Do not run `down --volumes` against data you need to keep.

## Production gate

This repository supplies deployment configuration, not an authorized deployment. Before an external release, provide TLS and a trusted proxy, set `DJANGO_DEBUG=false`, exact `DJANGO_ALLOWED_HOSTS`, HTTPS CSRF origins, a unique secret, and managed PostgreSQL credentials. Enable `DJANGO_TRUST_X_FORWARDED_PROTO` only when the trusted ingress strips client-supplied forwarding headers. Run `manage.py check --deploy` in that exact environment.

The local Compose file deliberately uses HTTP development cookies. It must not be exposed publicly. Serve Django administrative static assets from an explicit static-files service before exposing admin. Keep legacy routes disabled in the deployed profile. Session reset, revocation, invitation, and production operator policy remain release work.

The production-settings probe retains Django warning `security.W021` because HSTS preload is disabled. The public domain and its subdomains have not been approved. Do not enable preload merely to remove a warning. The local CI probe fails on errors and displays this warning. Before deployment, explicitly decide the preload policy and review all warnings in the real configuration.

The new workspace does no background quant computation. Celery broker and result settings are retained for later jobs. No worker or beat is launched by default. Use a separate durable broker from the evicting cache when introducing accepted jobs. Preserve model artifacts and research results until migration criteria are met.

The research Python client sends a required `X-Cadrisyn-Research: 1` header with staff Basic authentication. Ordinary browser Basic-auth requests cannot invoke research routes. Cross-origin pages cannot add this header without a successful CORS preflight, which the default profile denies. The header is a request-context guard, not a secret or a substitute for staff credentials. Browser session authentication still requires CSRF.

`CADRISYN_EOD_GRACE_HOURS` controls the historical-data freshness delivery window, with integer values from 0 to 48 and a personal-research default of 4. Agree a value with the actual licensed provider before release. Redis cache failures return an explicit 503 error, including failures encountered by API throttling. Market failures never substitute synthetic prices.

## Recovery and evidence

Back up PostgreSQL with `pg_dump` to encrypted storage. Restore into an isolated database and verify migrations, user counts, watchlist ownership, snapshot hashes, and a sign-in journey before setting an RPO or RTO claim. This rehearsal is outstanding. Do not migrate the original research SQLite file in place.

Health is `/health/`. API errors return a safe code and request ID. Unexpected API failures log a correlated server exception without returning its traceback to the browser. Centralized log redaction, metrics, alert routing, trace sampling, retention, and cost/load measurements remain production gates. Never log request bodies or credentials in infrastructure access logs.

CI configuration runs the supported workspace suite, schema drift check, frontend checks, and browser acceptance. Adding the workflow does not establish a remote green CI run. The preserved scientific stack needs a separate Linux compatibility job before advanced features can ship.

CI builds Next.js before the explicit TypeScript check so generated Next route types exist on a clean checkout. The browser job starts the production-built frontend itself and refuses to reuse another frontend server. On Windows, stop a running standalone preview before rebuilding; its process can hold `.next/standalone` files open.

## Official implementation references

The [Next.js self-hosting guide](https://nextjs.org/docs/app/guides/self-hosting) recommends a reverse proxy. The [Next.js deployment guide](https://nextjs.org/docs/app/getting-started/deploying) documents Node and standalone container output. The [Django 5.2 deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) defines deployment checks and secure production settings. These guides support the configuration choices. They do not establish that the local images or deployment have been tested.

The [Lightweight Charts README](https://github.com/tradingview/lightweight-charts/blob/master/README.md) specifies attribution requirements. Keep the chart attribution link and bundled notices when distributing the frontend.

The initial DRF 3.16.1 audit found five published vulnerabilities. The supported workspace now pins 3.18.3, following the [official DRF releases](https://github.com/encode/django-rest-framework/releases). The post-update package audit and size-limit regression are recorded separately from the initial findings. The preview nginx pin follows the security fixes in the [official 1.28 changelog](https://nginx.org/en/CHANGES-1.28). Container image scanning and digest pinning remain unverified until a Docker-capable build.
