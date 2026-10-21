## 2024-03-20 - ARIA labels for dynamic icon-only components
**Learning:** Game tasks using only SVG symbols (like Task 1 components) are completely invisible to screen readers without ARIA labels.
**Action:** Always verify if dynamically generated `<button>` elements with icon components (e.g., `<SymbolIcon>`) have an `aria-label` providing text alternatives. Also, use `aria-pressed` for selectable states.
## 2024-10-18 - [ARIA Pressed states on Toggle Buttons]
**Learning:** Vue state toggles can easily lack proper accessibility state tracking. If a button's main purpose is to toggle state and it uses an `active` class to visually represent it, it should always also have `aria-pressed`.
**Action:** Always verify if visual 'active' classes on buttons are accompanied by their accessibility counterpart `aria-pressed`.
