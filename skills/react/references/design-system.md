# Design System

## Token foundations

Define design decisions once, reference everywhere. Three layers:

1. **Reference tokens** — raw values (`color.blue.500 = #2563eb`, `space.4 = 16px`).
2. **System tokens** — semantic roles (`color.surface.primary`, `color.text.inverse`, `space.gutter`).
3. **Component tokens** — `button.primary.bg = color.surface.accent`.

Components consume system or component tokens, never raw values. Theming = swapping the reference→system mapping.

## Extensible primitives

A primitive (`Box`, `Text`, `Stack`) exposes:

- A small, semantic prop surface (`padding`, `align`, `gap`).
- Pass-through of native props via `...rest`.
- `forwardRef`.
- An `as` / polymorphic prop (or a `Slot` pattern à la Radix) to change the rendered element while keeping styling.

```tsx
<Box as="section" padding="lg" surface="primary" ref={ref}>
  ...
</Box>
```

Higher-level components are built _from_ primitives, never re-implementing token math.

## Encapsulating styles

Pick one approach per system and stick to it:

- CSS variables for tokens (works with any styling tech).
- CSS Modules / vanilla-extract / Tailwind for component styles.
- `cva` (class-variance-authority) or similar for variant management.

Components must not leak styling decisions to consumers (no inline `style` props that override tokens).

## Spacing & layout patterns

- **Stack**: vertical flow with a `gap` token; consumers don't write `margin`.
- **Inline**: horizontal flow with wrap + gap.
- **Center** / **Cluster** / **Sidebar** — named layout primitives (see Every Layout).
- **Layers**: positioning via stacked absolute children with consistent z-index tokens.

## Patterns for complex styles

- Variants → `cva({ base, variants, defaultVariants })`.
- Slots → expose `slotProps` or compound subcomponents.
- Polymorphism → `as` prop typed with conditional types (see [typescript.md](typescript.md)).
- Theming → CSS variables under `[data-theme="dark"]`.

## Anti-patterns

- Components that accept arbitrary `style` props for layout decisions.
- Multiple sources of truth for tokens (Figma diverging from code).
- Subcomponents reaching into internal classnames of parents.
- Variant explosion (`isPrimaryAndSmallAndLoading`) — combine via `cva`, not boolean props.
