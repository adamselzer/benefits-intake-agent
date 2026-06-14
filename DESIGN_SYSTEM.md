# Civic — a design system in the USWDS lineage, elevated

The caseworker front-end (`web/`) is built on a small design system called **Civic**.
It is a deliberate derivative of the [U.S. Web Design System](https://designsystem.digital.gov/)
(USWDS): it keeps the qualities that make government interfaces trustworthy and
accessible, and refines them past what a government site would actually ship. The
goal is something a veteran design engineer recognizes as "in the canon," done with
more care than the canon usually gets.

This document is the outlay of the system: what it inherits, what it changes and
why, and the full token and component reference. The `Design system` tab in the app
renders the same system in its own language.

## What it inherits from USWDS (the canon)

- **An open, civic typeface.** USWDS ships on Source Sans (and its sibling
  Public Sans). Civic uses **Source Sans 3** for all UI and body text. It reads as
  a public-sector interface, not a startup landing page.
- **Grade-based color tokens in semantic roles.** USWDS separates *system* colors
  (families × grades) from *theme* colors (roles: base, ink, primary, accent-cool,
  accent-warm, plus state colors). Civic keeps the role structure and the grade idea
  (darker / DEFAULT / lighter per family).
- **An 8px spacing scale.** USWDS spacing is multiples of 8px. Civic uses the same
  base unit and a numeric scale (`s-1` = 8px, `s-2` = 16px, …).
- **The signature components.** USWDS's summary box, alert, tag, and step indicator
  are the components that carry government UIs. Civic implements all four.
- **Accessibility first.** Color pairings clear WCAG AA contrast; every interactive
  element has a visible focus ring; nothing relies on color alone (icons and text
  accompany every state).

## What it elevates (past what government ships)

| Decision | USWDS default | Civic | Why |
|---|---|---|---|
| Display type | Merriweather, rarely used well | **Source Serif 4** for display headings | A serif used with intent signals editorial care; the Source super-family keeps it cohesive with the body sans. |
| Primary color | Saturated federal blue (`#005ea2`) | **Evergreen `#1F6F5C`** | Calmer and more humane than institutional blue, still unmistakably civic. |
| Canvas | White / cool gray | **Warm paper `#FBFAF8`** | Softer, less clinical; easier on the eye for long case review. |
| Type scale | Broad, utilitarian | **Tighter ~1.2 modular scale** | More refined hierarchy; less shouting. |
| Density | Generous, form-first | **Considered, content-first** | Optimized for reading a determination, not filling a form. |

The line it holds: every change is a refinement within the idiom, not a departure
from it. A government team could adopt Civic without leaving the hymnal.

## Tokens

### Type roles
- `--font-sans` Source Sans 3 — UI and body
- `--font-serif` Source Serif 4 — display headings, lead paragraphs
- `--font-mono` Roboto Mono — ids, citations, dollar figures (the audit artifacts)

### Type scale
`--text-xs` 11.5 · `--text-sm` 13 · `--text-md` 15 (base) · `--text-lg` 17 ·
`--text-xl` 20 · `--text-2xl` 25 · `--text-3xl` 31. Body line-height 1.55–1.66.

### Color — theme roles
- `--ink` `#14181F` · `--base-dark` `#3D4654` · `--base` `#697078` ·
  `--base-light` `#A6AAB0` · `--base-lighter` `#DAD6CC` · `--base-lightest` `#F4F2EC`
- `--paper` `#FBFAF8` · `--surface` `#FFFFFF`
- `--primary-darker` `#143F35` · `--primary-dark` `#1A584A` · `--primary` `#1F6F5C`
  · `--primary-light` `#6BA597` · `--primary-lighter` `#E4F0EC`
- `--accent-cool` `#356A82` · `--accent-warm` `#A86F2C`

### Color — state (each with a tint for backgrounds)
- `--info` `#2E647F` / `--info-bg` `#E7EEF2`
- `--success` `#1F6F5C` / `--success-bg` `#E4F0EC`
- `--warning` `#8A5314` / `--warning-bg` `#F6ECD8`
- `--error` `#963232` / `--error-bg` `#F6E7E4`

### Spacing — 8px base
`--s-05` 4 · `--s-1` 8 · `--s-2` 16 · `--s-3` 24 · `--s-4` 32 · `--s-6` 48 · `--s-8` 64

### Radius & focus
`--radius-sm` 6 · `--radius-md` 10 · `--radius-lg` 14 · focus ring `0 0 0 3px rgba(31,111,92,0.35)`

## Components

- **Summary box** — tinted panel with a primary left rule; carries the headline
  recommendation.
- **Alert** — left accent bar + tinted background + icon, in four states
  (info / success / warning / error). Used for review items and status.
- **Tag** — small labeled chip for provenance (source document), citations (mono),
  and scenario labels.
- **Step indicator** — numbered steps with connectors and an emphasized current
  step; renders the agent pipeline (ingest → extract → screen → route).
- **Button** — filled primary and outline default.
- **Card** — surface with a hairline border and `radius-md`.

## Where it is applied

Civic is implemented in `web/static/styles.css` as CSS custom properties (the
tokens) plus component classes, and shown end-to-end in the caseworker UI. The
portfolio's Streamlit apps carry the same palette and type direction for family
resemblance, but the full component system lives here, where a hand-built front-end
can express it.

## Sources

- USWDS: [typography](https://designsystem.digital.gov/design-tokens/typesetting/font-family/),
  [color tokens](https://designsystem.digital.gov/design-tokens/color/overview/),
  [spacing units](https://designsystem.digital.gov/design-tokens/spacing-units/),
  [components](https://designsystem.digital.gov/components/overview/).
