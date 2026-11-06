# Custom Hooks

Default reuse unit for stateful behavior. A custom hook is _any_ function whose name starts with `use` and which calls other hooks.

## When to extract

- Two components share state + effect logic.
- A component's hook calls cover more than one concern — split one out.
- Behavior needs unit tests independent of the UI.

## Shape

```tsx
function useDebouncedValue<T>(value: T, ms: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return debounced;
}
```

## Naming + return shape

- Verb-first if it performs an action (`useToggle`, `useFetch`).
- Noun-first if it reads (`useUser`, `useViewport`).
- Return a tuple when order is obvious (`[value, setValue]`).
- Return an object when there are 3+ fields or naming clarifies usage (`{ data, error, isLoading }`).

## Loading hooks (pre-React-Query)

`useFetch`, `useUser`, `useResource<T>` — model the four states `idle | loading | success | error` and abort on unmount. If the codebase already uses React Query / SWR, lean on them instead.

## Anti-patterns

- Hook that takes an unstable callback and depends on it in `useEffect` — wrap in `useEvent` / `useEffectEvent`, or memoize at the call site.
- Hook returning new object identity each render when callers depend on identity — memoize the return.
- Hooks called conditionally (rules of hooks violation).
- "God hook" returning 12 fields — split.
