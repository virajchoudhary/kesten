# Third-party notices

Application source and third-party dependency licenses are separate. This publication does not introduce a new blanket license for the repository or relicense third-party code/data. Review the pinned packages and their included notices before reuse.

| Component | Upstream license | Use |
| --- | --- | --- |
| TradingView Lightweight Charts | Apache-2.0 | Daily market charts. Required TradingView attribution remains visible; Kerquant is not affiliated with TradingView. |
| Inter | SIL Open Font License 1.1 | Self-hosted interface typography through `@fontsource-variable/inter`. |
| IBM Plex Mono | SIL Open Font License 1.1 | Self-hosted prices, dates, and identifiers through `@fontsource/ibm-plex-mono`. |
| Lucide | ISC | Interface icons. |
| Radix UI | MIT | Accessible UI primitives. |
| Django | BSD-3-Clause | API and account framework. |
| React and Next.js | MIT | Frontend application framework. |

Exact versions are in `web/package-lock.json` and the backend lock files. Package-distributed license files remain with installed dependencies. Upstream references include [Lightweight Charts](https://github.com/tradingview/lightweight-charts), [Inter](https://github.com/rsms/inter), [IBM Plex](https://github.com/IBM/plex), [Lucide](https://github.com/lucide-icons/lucide), and [Radix](https://github.com/radix-ui/primitives).

`deploy/vendor/gosu-release-key.asc` is an upstream PGP public release-verification key. It contains no private key and is retained for build integrity. It is not a local TLS certificate or credential.

No market-data rows, licensed historical archive, model archive, or investment-performance claim is supplied by these notices. The demo's observations and displayed research results are synthetic.

This publication distributes source, not built container images. Before distributing images, inspect their final contents and include the applicable Gosu Apache-2.0 notice, optional sharp/libvips LGPL-3.0-or-later requirements, and caniuse-lite CC-BY-4.0 attribution. The CI recipes build images for isolated testing and do not push them to a registry.
