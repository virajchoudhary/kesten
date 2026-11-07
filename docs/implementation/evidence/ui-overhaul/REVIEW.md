# Independent review record

Reviews were bounded and read-only. They did not change source, access credentials/databases, run browser acceptance, or certify a production deployment. Reviewer labels identified GPT-6 Luna; provider/effort routing attestation was unavailable.

| Review | Verdict | Evidence and disposition |
| --- | --- | --- |
| Initial design comparison | Complete, design only | Confirmed the existing three-column layout and fixed chart height. Compared a switchable market canvas with a bottom research dock. The final implementation chooses the switchable view because the current result tables and replay controls need width and readable vertical space. |
| Engineering, integrity and accessibility source review | FAIL before correction | Found Unicode corruption in history metadata; active Research navigation dropped saved query identities; the client accepted delayed provenance for a Demo request. Corrected all three. A focused unit test reproduced the provenance failure before correction. |
| Same review, responsive controls | Corrected at inspection | Verified the named mobile Indicators button and separate mobile/desktop watchlist expanded states. No added comments or lint/TypeScript suppressions were found. |
| Final source correction review | PASS | Verified provenance rejection in both directions, exact embedded research query preservation and the Radix mobile dialog trigger. This was a source review, not an independent E2E execution. |
| Final desktop/integrated visual review | PASS with snapshot limit | Desktop and integrated research images were coherent. The then-supplied phone image predated the Account-access fix, so the reviewer did not accept it as current phone evidence. |
| Fresh phone/desktop visual review | PASS | Inspected current production-mode 390px markets/research and 1440px markets images. Account access, chart prominence, readable fixture disclosures and unclipped research controls were visible. The verdict covers those images, not accessibility certification. |

The initial engineering reviewer asserted a requirement for zero letter spacing. The repository's typography section contains no such rule. Numeric compression was removed for price legibility; the intentional wordmark/heading treatment remains documented in the revised design system.

Parent-owned browser verification then reproduced a separate Back-navigation defect. A local selected-instrument state overrode the restored URL. Removing that redundant state makes the parsed URL authoritative. The terminal scenario now exercises switching symbols, Back, returning to research, saving, reloading and retaining the active selection. Parent visual review also corrected 320px header overflow and a clipped public navigation label. These corrections require the recorded final browser gates; the earlier independent verdict is not presented as an independent rerun of those later changes.

Repeated rapid exploratory runs hit the configured API budgets. A misconfigured gateway-health attempt also targeted `/health/` on the direct Next.js server. Those failures remain in private local logs. The final serial runner uses the direct-frontend configuration and waits for rate windows between suites. It changes no application security policy, assertion, response, retry count or data-provider restriction.
