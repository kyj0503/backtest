# Frontend Design Refresh Plan

## Context
- **Scope**: UI polish refresh for the shadcn/ui based frontend while retaining all existing flows, data density, and functionality.
- **Drivers**: Improve visual hierarchy, consistency, and theme utilization without reworking backend integrations or altering API contracts.
- **Constraints**: Preserve component structure, avoid new dependencies beyond shadcn/ui ecosystem, keep accessibility and responsiveness intact.

## Design Goals
1. Maintain feature parity and data presentation while elevating perceived quality.
2. Align all styling with the dynamic theme system (`frontend/src/themes`, `useTheme.ts`).
3. Improve typography, spacing, and interaction states using shadcn/ui primitives.
4. Enhance chart readability and ancillary surfaces (tables, alerts) through token-driven styling.

## Workstreams
### 1. Token & Theme Refinement
- Audit current color/typography tokens in `frontend/src/index.css` and theme JSON files.
- Introduce richer accent palettes, improved shadow scale, and consistent radius definitions.
- Document global typography scale (display/headings/body/mono) for reuse.

### 2. Global Shell Enhancements
- Update `components/Header.tsx` and layout containers for better depth, sticky behavior, and theme selector presentation.
- Ensure loading overlays, alerts, and dialogs leverage shadcn transitions and maintain ARIA compliance.

### 3. Form & Control Polish
- Normalize section layouts across `PortfolioForm`, `StrategyForm`, `CommissionForm`, etc., using shadcn form components.
- Apply consistent input states (focus, hover, disabled) and inline validation feedback through `FormMessage`.
- Introduce micro-interactions (button/trigger hover, subtle scale) via variant props and Tailwind utilities.

### 4. Results & Chart Presentation
- Wrap statistics in responsive grids with card variants and highlight treatments.
- Standardize chart containers with shared headers/footers, refreshed legends, and theme-driven palettes.
- Improve tooltips and annotations using existing `Tooltip`/`Popover` abstractions.

### 5. Supporting Surfaces
- Refresh tables (trades, allocations) using shadcn `Table` spacing defaults and theme tokens for zebra striping.
- Refine alerts, empty states, and badges with iconography and consistent spacing.

## Implementation Sequencing
1. Token/theme updates (Workstream 1).
2. Global shell adjustments (Workstream 2).
3. Form/control polish (Workstream 3).
4. Results and chart styling (Workstream 4).
5. Supporting surfaces (Workstream 5).

## Verification Strategy
- After each workstream: run `npm run lint`, `npm run test`, and, if applicable, `./scripts/test-runner.sh frontend`.
- Manual regression: verify Backtest flow under each built-in theme and both light/dark modes.
- Capture before/after screenshots for primary screens to confirm visual improvements without layout regressions.

## Risks & Mitigations
- **Style regressions**: isolate changes per workstream, use incremental commits/PRs.
- **Chart readability**: validate color contrast with theme tokens before release.
- **Responsive issues**: test main breakpoints (mobile/tablet/desktop) after each major update.

## Deliverables
- Updated theme tokens and component styles.
- Revised documentation snippets (if component APIs change).
- TODO checklist aligned with sequencing for ongoing tracking.
