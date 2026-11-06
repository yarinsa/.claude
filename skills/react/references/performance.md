# Performance Optimization

**Profile first.** React DevTools Profiler + browser flame chart. Don't memoize blind.

## Code splitting

Split at route boundaries first, then heavy widgets (charts, editors, PDF viewers).

```tsx
const Editor = lazy(() => import('./Editor'));

<Suspense fallback={<Skeleton />}>
  <Editor />
</Suspense>;
```

Always pair `lazy` with an error boundary — `import()` can reject (chunk load failure, deploy mid-session).

## When `useCallback`/`useMemo` actually help

They help only when the memoized identity is _consumed_ downstream by:

- `React.memo`'d component comparing props.
- A hook's dep array.
- An effect that should not re-run.

Wrapping a callback that is passed to a native `<button onClick>` does _nothing_ useful; the DOM doesn't care about identity.

```tsx
// helpful: Heavy is memo'd; identity stability matters
const onSelect = useCallback((id) => setSel(id), []);
<Heavy onSelect={onSelect} />;

// pointless: button doesn't care
const onClick = useCallback(() => doIt(), []);
<button onClick={onClick} />;
```

## `React.memo`

Memoize a child only when:

- It re-renders frequently due to parent re-renders.
- Its render is non-trivial.
- Its props can be compared cheaply.

Pass `arePropsEqual` only when default referential equality is insufficient and a deep check is cheaper than the render.

## Context performance

Every consumer re-renders when the context value identity changes. Mitigations:

- Split contexts (see [clean-code.md](clean-code.md)).
- Memoize the provider value.
- Use `use-context-selector` to subscribe to a slice.

## List rendering

- Stable keys.
- Virtualize lists >~100 visible rows (`react-virtual`, `react-window`).
- Memoize row components if they render anything non-trivial.

## Render scheduling

- `startTransition` for non-urgent updates (search input → result list).
- `useDeferredValue` for cheap downstream rendering of a fast-typed value.
- `Suspense` for IO-bound data with React Query / RSC.

## Anti-patterns

- Wrapping every component in `memo` "just in case".
- `useMemo`/`useCallback` with deps that change every render — strictly slower than no memo.
- Sorting/filtering large arrays inside JSX without memoization.
- Object/array literals in JSX passed to a memo'd child (breaks memo).
