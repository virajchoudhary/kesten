# Independent research usability review

The coordinator delegated bounded, read-only audits and implementation closure. Requested worker route: configured Azure Luna Max. Provider attribution was not independently attested: `ROUTING_UNVERIFIED`. These records do not claim independent providers or a hardened read-only sandbox.

## Initial workflow audit

The auditor read the implementation and found hidden dataset coverage/source metadata, unavailable receipt inspection, older-run metadata depending on the capped picker, and a saved baseline MAE delta missing from the visible table. It recommended a lazy owner-private endpoint reusing `verify_intake`, with no raw archives, and unchanged admission/scientific contracts. It ran no tests and made no edits.

## Implementation review: FAIL, two P2 findings

1. The API returns only the newest 100 datasets while local search appeared complete. The correction discloses the limit, scopes no-match language to the available list, and retains exact-ID provenance access for older saved runs. Pagination was not added.
2. Generated TypeScript used `Omit<ResearchIntakeProvenance, "status">`, losing useful variant fields. The correction removes the optional OpenAPI discriminator annotation while retaining required status-specific `oneOf` shapes and read-only serialization. The exhaustive type regression failed before the correction and passed afterward.

The reviewer independently ran TypeScript, scoped ESLint and 14 focused UI tests. Owner isolation, archive non-disclosure, exact identity binding, operator-attestation limitations and baseline context were accepted. PostgreSQL and the new real-browser workflow were outside its execution scope.

## Bounded closure: PASS

The closure reviewer reported **Standards PASS, zero findings; Spec PASS, zero findings** for the two corrections. It independently regenerated TypeScript to stdout using installed `openapi-typescript` 7.13.0 and compared it in memory with `generated.ts`: exact match. It checked the three schema variants, the 100-item limit and newest ordering, exact owner-scoped access, strict false source-qualification schema, and exhaustive narrowing test.

It independently ran current TypeScript, targeted ESLint and diff checks. It inspected the recorded 134-test frontend pass and the existing research browser closure. It did not rerun PostgreSQL or claim final mobile regression acceptance.

## Parent acceptance of the remaining mobile issue

After the independent review began, the parent found that the baseline jump placed the heading behind sticky navigation. The browser bounding-box assertion failed before the fix: expected heading Y >= 45, actual 0.296875. The `scroll-mt-16` correction passed the same assertion in dark and light mobile themes against the final standalone build. See `mobile-anchor-before.txt`, `browser-final.txt`, and the final mobile screenshots.

The parent inspected current files, actual test receipts, source identities and screenshots. It verified the PostgreSQL worker's recorded source hashes and clean teardown, then committed only the concurrency test fix separately. Research source qualification and production release remain NO-GO. No reviewer changed numerical code, archives or existing databases.
