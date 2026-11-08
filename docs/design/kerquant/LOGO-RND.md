# Kerquant logo research and development

Date: 8 November 2026. The user rejected the thin K and then the solid split K. Both attempts assumed the first letter needed to carry the identity. The next pass removed that assumption and explored symbols and lettering independently. This is product identity work, not a trademark clearance report.

## Research findings and limits

[Jane Street's official site](https://www.janestreet.com/) presents a research-driven identity and expressly identifies its concentric-circle mark as a registered trademark. That symbol is excluded from Kerquant's exploration. The useful principle is that a brand can use a memorable abstract shape without turning its first letter into an icon. This is a design inference, not evidence that an abstract shape alone creates trust.

[Two Sigma's official site](https://www.twosigma.com/) foregrounds hypothesis and scientific inquiry. For Kerquant, the relevant lesson is to express a research process without suggesting financial returns. The new mark therefore uses reference frames and a plane, rather than candles, growth arrows, sigma lettering, coins, or trading imagery. No affiliation or comparable financial performance is implied.

The [LSEG lettering project by its type designer](https://stuff.xyztype.com/custom/project/lseg_motto) was identified in search results, but its page timed out in the direct reading tool. The official partner-brand PDF link redirected to a partner page. The MSCI logo-usage PDF returned 404. Those assets were not treated as inspected visual guidelines or copied. Exact-mark conflict searching and legal review remain open.

## Exploration and selection

The built-in image-generation tool produced a four-direction monochrome exploration board. It was a concept artifact, not an application asset or a finished vector file. No third-party logo was supplied as an image input. The [prompt](assets/logo-rnd-prompt.txt) records the creative constraints.

| Direction | Design judgment | Decision |
| --- | --- | --- |
| 01, Aperture | Strong compact shape, but its camera/shutter associations were less specific to research. | Not selected. |
| 02, Measured frame | Distinct from the rejected monograms; offset boundaries and a plane fit the idea of observations and reference relationships. | User selected this direction in the four-option review. |
| 03, Custom wordmark | A typographic route with a distinctive q, but the separate icon would depend heavily on the letter treatment. | Not selected. |
| 04, Interlocking planes | Compact and bold, but its diagonal rhythm risked a bolt or crypto association. | Not selected. |

These are design judgments, not measured consumer-recognition results. The user's direction selection does not establish legal clearance for the symbol.

## Production construction

The [standalone SVG](assets/kerquant-symbol.svg) uses a 32×28 coordinate system. Two open right-angle frames surround a central parallelogram. The frame strokes are three units wide, and their spacing is explicit rather than depending on a stroked outline. This keeps the artwork predictable when rasterized at small sizes.

`BrandMark` supplies the symbol to the public, terminal, and account headers. The account header previously contained a separate three-bar glyph; it now uses the shared component. The favicon repeats the same path on a dark tile. Interface colors remain separate from the mark, which uses neutral foreground colors in both themes. The wordmark retains the existing self-hosted Inter family; no new font dependency or license is introduced.

The generated board is preserved as R&D. The application consumes deterministic vector code, not the generated raster. Header and favicon shapes, metadata, theme treatment, small-size rendering, mobile overflow, and account consistency are checked in Chromium. The [verification record](VERIFICATION.md) identifies the exact tested source and remaining limitations.
