# Higher-Order Components

A HOC is a function `Component -> Component`. Use sparingly — hooks cover most of the same ground with less ceremony.

## Still legitimate uses

- **Wrap-time injection**: providing data/context/permission _before_ the wrapped component renders.
- **Lib boundaries** where a hook can't reach (legacy class components, third-party libs that consume a component).
- **Route-level guards**: `withAuth(Page)`, `withFeatureFlag('beta', Page)`.

## Shape

```tsx
function withAuth<P extends object>(Inner: ComponentType<P>) {
  return function Wrapped(props: P) {
    const user = useCurrentUser();
    if (!user) return <Redirect to="/login" />;
    return <Inner {...props} />;
  };
}
```

Rules:

- Forward all props.
- Hoist statics if needed (`hoist-non-react-statics`).
- Preserve display name: `Wrapped.displayName = \`withAuth(\${Inner.displayName ?? Inner.name})\``.
- Forward refs with `forwardRef` if the inner accepts them.

## When to prefer a hook

If the wrapper is just _running logic and reading state_, a hook is simpler:

```tsx
function Page() {
  const user = useRequireAuth(); // throws/redirects internally
  ...
}
```

## Anti-patterns

- Stacking 4 HOCs (`withRouter(withAuth(withTheme(withAnalytics(Page))))`) — combine into a single Provider/hook pair.
- HOC that swallows or rewrites props in non-obvious ways.
- HOC that introduces a new context without exposing a hook to read it.
