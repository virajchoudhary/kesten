# Browser evidence

Before images are original in-app Chromium captures. Their actual image dimensions are retained below; browser chrome, scrollbars and available capture area differ. After images come from the compiled application in Playwright Chromium. These are observations of the application, not design mockups or generated images.

## Chart workspace

The chart, compact toolbar, watchlist, study readouts, provenance strip and integrated research entry remain the primary terminal. The mobile settings correction removes an empty stretched panel while retaining bounded access to every setting.

Before desktop, 1440 x 810 capture:

![Market workspace before](evidence/before-1440.png)

After desktop, requested viewport 1440 x 900:

![Market workspace after at 1440](evidence/after-markets-1440.png)

After desktop, requested viewport 1920 x 1080:

![Market workspace after at 1920](evidence/after-markets-1920.png)

Preserved chart depth exercised by the real browser suite, including log scale, studies, a level, session measurement and indexed Demo comparison:

![Customized chart analysis](evidence/after-custom-analysis-1920.png)

Integrated research remains native to the market workspace, with exact saved-run provenance and separate synthetic results:

![Integrated research dock](evidence/after-research-dock-1920.png)

After tablet, requested viewport 820 x 1180:

![Market workspace after on tablet](evidence/after-markets-820.png)

After phone settings, requested viewport 390 x 844:

![Compact chart settings retain plot context](evidence/after-mobile-settings-context.png)

The baseline settings geometry is recorded in `product-browser-before.txt`. There is no separately retained before-settings image in this package; the ordinary before-market image is not evidence of that panel's open state.

## Research navigation

Before Open changed the selected result but left the viewport in the registry, 375 x 812 capture:

![Saved result remained above the viewport](evidence/before-history-open-390.png)

After the selected result is brought into view by the exact result fragment. The browser scenario subsequently activates Saved runs and captures its destination:

![Exact saved result brought into the phone viewport](evidence/result-open-390.png)

![Research section navigation at saved runs](evidence/after-mobile-history-navigation.png)

The viewport assertion for the selected Evaluation results heading runs before navigating back to Saved runs. This screenshot alone does not prove the selected-heading assertion; the browser log and test provide that evidence.

Standalone research after, requested viewport 1440 x 900:

![Research workspace after](evidence/after-research-1440.png)

## Shared account navigation

Before, 390 x 844:

![Account before lacked shared terminal controls](evidence/before-account-390.png)

After, 390 x 844 with theme changed through the actual header control:

![Account after with shared header](evidence/after-mobile-account-navigation.png)

The complete local capture set includes Markets, Research, Account, Data and Methodology at 1440 x 900, 1920 x 1080, 820 x 1180 and 390 x 844, plus desktop/mobile sign-in. Full-page image height can exceed the requested viewport. The retained manifest records requested dimensions, route titles, overflow checks and source identity.

## Review disposition

The parent reviewed the complete 22-image contact sheet and focused market, research, settings, account, saved-result, customized-chart and dock captures. No additional blocking overflow, obscured required control or misleading provenance was observed. The screenshots support this bounded disposition; they do not establish every possible interaction state.

The separate visual review's one low-severity mobile legend finding was triaged against a real native-keyboard check. The final study values remain reachable through the existing scrollable, focusable legend, as shown below. No code change was needed for that finding. See the verification record for the original FAIL verdict and its limits.

![Mobile study legend after native keyboard scrolling](evidence/legend-keyboard-390.png)

![Contact sheet of final primary routes](evidence/final-contact-sheet.png)

Firefox, WebKit and physical-device touch behavior remain unverified. An axe or browser-test pass is not a claim of full WCAG conformance or professional-terminal feature parity.
