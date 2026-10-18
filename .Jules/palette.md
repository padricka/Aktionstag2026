## 2024-03-20 - ARIA labels for dynamic icon-only components
**Learning:** Game tasks using only SVG symbols (like Task 1 components) are completely invisible to screen readers without ARIA labels.
**Action:** Always verify if dynamically generated `<button>` elements with icon components (e.g., `<SymbolIcon>`) have an `aria-label` providing text alternatives. Also, use `aria-pressed` for selectable states.
