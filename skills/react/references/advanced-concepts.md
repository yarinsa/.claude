# Advanced Concepts & Hooks

## Portals

Render into a DOM node outside the parent hierarchy without leaving the React tree. Events still bubble through the React tree, not the DOM tree.

Use for: modals, toasts, tooltips, dropdown menus that must escape `overflow: hidden` or stacking contexts.

```tsx
return createPortal(<Toast>...</Toast>, document.body);
```

## Error boundaries

Class component that catches render-phase errors in its subtree. There is no hook equivalent yet — keep one small class component (or use `react-error-boundary`).

- One per route + one around each "risky" widget (charts, third-party embeds).
- Reset the boundary on route change.
- Errors in event handlers, timers, and async code are NOT caught — handle there explicitly.

## Keys

Keys identify list items across renders. Wrong keys = wrong reconciliation = lost state, wrong animations.

- Use stable ids. `index` is only OK if the list is static and never reordered.
- Changing a key on the same component is a forced remount — sometimes intentional (form reset by user id).
- Sibling components with the same key collide; siblings must have unique keys.

## Refs & forwardRef

- `useRef` for mutable values that don't trigger re-render.
- `useImperativeHandle` to expose a narrow API from a child component.
- `forwardRef` to forward refs through abstraction layers — required for design-system primitives.

```tsx
const Input = forwardRef<HTMLInputElement, InputProps>((props, ref) => <input ref={ref} {...props} />);
```

## Lazy & Suspense

`React.lazy(() => import('./Heavy'))` + `<Suspense fallback={...}>`. Lazy at route boundaries by default, then individual heavy widgets. Wrap with error boundary too — lazy can reject.

## Hydration mismatches

Server and client must render identical markup on first pass. Anything time/random/locale dependent must be deferred to `useEffect` or rendered behind a `useSyncExternalStore` snapshot that the server can provide.
