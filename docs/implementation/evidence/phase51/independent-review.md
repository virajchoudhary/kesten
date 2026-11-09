# Independent Phase 5.1 review

Separate read-only Codex verifier passes inspected the qualification code, actual receipts and source boundaries. The configured verifier role uses Azure Luna Max; backend/billing routing was not independently attested. Verifiers did not implement the changes they graded.

## Findings and corrections

| Finding | Correction | Verification |
| --- | --- | --- |
| Checking only CREATE on public omitted database-level CREATE and other writable schemas. | The probe checks explicit role, database and schema capabilities. | Pure guard tests plus actual source/restored runtime queries. |
| USAGE-based membership and pg_class ownership checks missed NOINHERIT/SET role switching and ownership of routines/types. | Replaced partial enumeration with a dedicated-role invariant. No role memberships are allowed, and pg_shdepend ownership dependencies cover current-database and shared objects. | Four real transactional PostgreSQL tests demonstrate a benign role, SET-capable NOINHERIT membership, routine ownership without relations and custom-type ownership without relations. No configured runtime role was changed or found overprivileged. |
| Evidence links pointed at receipts not yet curated. | Current receipts are now present in this directory. | Documentation-link check before commit. |

The reviews independently ran qualification unit tests and Ruff; the later reviewer also ran TypeScript and ESLint and inspected live image IDs/labels/users. It confirmed the recorded 154 backend tests, 16 restored-browser passes, 27-table/13-replay recovery evidence and restore refusal receipts. Its source checks corroborated the reviewed pricing/timing claims without legal or empirical approval.

The final corrected proof is version 2 and was exercised against another fresh restore target. Earlier incomplete attempts remain identified as failed or interrupted. The working restored browser database and the original source remain preserved.

## Final bounded acceptance

The fresh final verifier returned PASS for the corrected role boundary and current local files. It independently ran five pure qualification tests and Ruff, inspected the four real SQL regression cases and their nine-test combined execution receipt, parsed the final 27-table/258-row/13-replay snapshot and checked populated evidence links. It found no remaining defect in that bounded scope. It did not rerun SQL writes or read private admin credentials. Parent execution receipts establish those runtime results. Test execution and scoped source acceptance remain separate from production certification or forecasting qualification.
