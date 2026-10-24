# Bundled assets

No external CDN is required at runtime.

- Chart.js **4.4.8**, official UMD distribution from
  https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.js.
  MIT license: `CHART-LICENSE.md`. Distribution header preserved.
- Lucide **0.468.0**, 18 official SVGs from
  https://github.com/lucide-icons/lucide/tree/0.468.0/icons.
  Combined into `lucide.svg` symbols without changing path geometry;
  `shield-check.svg` is also used as a favicon. ISC/Feather attribution and
  license: `LUCIDE-LICENSE`.

Lucide SVGs use `currentColor`, a 24×24 viewBox, no fill and rounded stroke
joins/caps. Decorative icons are hidden from assistive technology; controls
retain text or accessible labels. No emoji or icon font is used.
