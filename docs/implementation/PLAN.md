# Cadrisyn stabilization and first workspace

Authorization: the owner provisionally approved the architecture and requested autonomous implementation of stabilization and the initial frontend. Cadrisyn is a temporary working name. Trademark/domain/repository naming, paid services, and deployment remain unapproved.

## Workflow

- [x] Read the poteto-mode principles and all blueprint, approval, and independent-review documents.
- [x] Phase A: Frame. Preserve the existing database and local work, then produce a working authenticated market workspace rather than a visual mockup.
- [x] Phase B: Design the workflow. Reuse the settled architecture instead of repeating a design arena. The approved smaller API/worker boundary is the implementation sketch.
- [ ] Phase C: Run the loop. Establish baseline, stabilize the API/import/configuration boundary, build market data and ownership contracts, integrate the frontend, and test real user paths.
- [ ] Phase D: Keep the audit trail. Record verifiable units and commit only explicit paths.
- [ ] Phase E: Verify and hand back. Run checks, independent review, startup/browser proof, and document actual entry points and remaining release gates.

Architect phases are Ground, Sketch, Agree, Implement, and Scrap. Ground/Sketch reuse the blueprint and contracts below. Agree is the owner's provisional approval. Implement proceeds now. Scrap applies only if actual integration disproves the chosen boundary.

The parallel work uses Frame, Fan out, Aggregate, and Report. Two Luna Max workers own disjoint backend stabilization and new `web/` outputs. The parent owns new market/auth/watchlist API, integration, startup/deployment files, hygiene, commits, and final acceptance. No worker changes branches or commits shared work. No model training or paid-provider calls are needed.

## Throughput and done predicate

Work in three implementation units after the blueprint-preservation commit: stabilization, functional market/API workspace, and reproducible verification/startup. Each unit ends with observed checks and an explicit-path commit. Existing ML/optimizer/options/RL/report modules remain available through the protected legacy research path; unresolved scientific defects do not become new product claims.

Done means a user can start the documented local services, sign in to an isolated development database, search/select an exchange-qualified stock, inspect daily candles and computed indicators/table, add/remove persistent private watchlist items, change theme/range, reload, and sign out. Demo and market data are distinct. Offline/provider/validation/authentication failures have visible outcomes. Relevant backend, security, type, build, unit, and browser checks pass or remaining environmental blockers are demonstrated and documented.

## Scope choices

Use the installed Node 22 LTS if compatible with the locked Next release, rather than change the user's global Node installation. Use a separate Python environment for the supported Django workspace, preserving the old quant environment. PostgreSQL-ready settings and containers are required; no claim of PostgreSQL/container execution without actual local evidence.

Keep the original `backend/db.sqlite3` untouched. A read-only SQLite backup was saved locally under the ignored evidence path. New local state uses `.local/cadrisyn.sqlite3`. No tracked virtual environment, model artifact, research dataset, or log is deleted. Hygiene uses ignore rules and removal from the Git index only where preservation is proved.

No provider entitlement was supplied. Default to deterministic synthetic fixtures, visibly labelled. An explicit market mode may use a bounded existing free-data adapter only when enabled, with timestamps/source/delay caveats. A provider failure returns unavailable and never becomes synthetic prices under a market label. External release still needs data rights.

## Integration contract

All paths are same-origin `/api/v1/` with trailing slashes. Sessions use Django cookies and CSRF. All market/watchlist endpoints require login. Errors are `{code,message,field_errors,request_id}`. Responses containing account data are private/no-store.

- `GET /session/` returns `{authenticated,user,csrf_token,market_data_enabled,legacy_enabled}`. User is null or `{username,is_staff}`.
- `POST /session/` accepts `{username,password}`, requires CSRF even for anonymous login, and returns the session envelope. `DELETE` logs out with CSRF.
- `GET /instruments/?query=` returns `{items: Instrument[]}`. Instrument has `id,symbol,name,exchange,currency,timezone`.
- `GET /instruments/{id}/bars/?range=1y&mode=demo` accepts `1m,3m,6m,1y,2y` and `demo,market`. It returns `{instrument,bars,indicators,provenance}`.
- Bar has `time` as an exchange-session date, plus numeric `open,high,low,close,volume`. Indicator arrays are `sma20,sma50,rsi14`, with `{time,value}` points.
- Provenance has `data_mode` (`demo` or `delayed`), `source_id,source_label,as_of,fetched_at,price_basis,freshness_state,market_state,delay_seconds,snapshot_id,disclaimer`.
- `GET /watchlist/` returns `{items: Instrument[]}`. `POST` accepts `{instrument_id}` and is idempotent. `DELETE /watchlist/{instrument_id}/` removes only the current user's entry.
- The parent produces `contracts/openapi.json`; `openapi-typescript` generates the frontend types. Runtime schema parsing validates untrusted JSON at the frontend boundary. Contracts are tested against actual API responses.

The UI has working Markets, data/methodology information, account/sign-out, and a protected legacy research entry only when configured. Do not add fake Portfolio/Backtest/AI pages to the new shell. Legacy functionality stays in its original modules and explicit optional startup path.
