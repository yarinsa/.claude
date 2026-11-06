# Example: refactor `UserDashboard` using container + custom hook

## Task

`UserDashboard` fetches the current user inline, manages loading/error UI, and renders the dashboard body. Tests are brittle because the component owns both the network call and the layout.

## Pattern(s) selected

- [container-components.md](../references/container-components.md) — extract data concern.
- [custom-hooks.md](../references/custom-hooks.md) — `useCurrentUser` hook.

## Why this pattern

Two signals:

1. Three pages already duplicate the same fetch + loading/error scaffolding.
2. The presentational dashboard is untestable without a network mock.

## Plan

- [ ] Add `features/users/useCurrentUser.ts` returning `AsyncState<User>`.
- [ ] Add `features/users/CurrentUserLoader.tsx` — render-prop container.
- [ ] `UserDashboard` becomes a pure component taking `user: User` prop.
- [ ] Route swaps to `<CurrentUserLoader>{(u) => <UserDashboard user={u} />}</CurrentUserLoader>`.
- [ ] Delete dashboard's `useEffect` + loading state.

## Before

```tsx
function UserDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);
  if (loading) return <Spinner />;
  if (error) return <ErrorBanner error={error} />;
  if (!user) return null;
  return <div>...dashboard for {user.name}...</div>;
}
```

## After

```tsx
// features/users/useCurrentUser.ts
export function useCurrentUser(): AsyncState<User> {
  const [state, setState] = useState<AsyncState<User>>({ status: 'loading' });
  useEffect(() => {
    const ctrl = new AbortController();
    fetchCurrentUser({ signal: ctrl.signal })
      .then((data) => setState({ status: 'success', data }))
      .catch((e) => {
        if (e.name !== 'AbortError') setState({ status: 'error', error: e });
      });
    return () => ctrl.abort();
  }, []);
  return state;
}

// features/users/CurrentUserLoader.tsx
export function CurrentUserLoader({ children }: { children: (u: User) => ReactNode }) {
  const s = useCurrentUser();
  if (s.status === 'loading') return <Spinner />;
  if (s.status === 'error') return <ErrorBanner error={s.error} />;
  return <>{children(s.data)}</>;
}

// features/dashboard/UserDashboard.tsx
export function UserDashboard({ user }: { user: User }) {
  return <div>...dashboard for {user.name}...</div>;
}

// routes/dashboard.tsx
export default function DashboardRoute() {
  return <CurrentUserLoader>{(u) => <UserDashboard user={u} />}</CurrentUserLoader>;
}
```

## Risks

- If React Query is already adopted elsewhere, prefer `useQuery(['currentUser'], fetchCurrentUser)` instead of hand-rolling — see [react-query.md](../references/react-query.md).
- `AsyncState<T>` must be exhaustively handled (TS `never` check) so future states (e.g. `'idle'`) cannot fall through silently.

## Verification

- [x] `pnpm typecheck`
- [x] `pnpm lint`
- [x] `UserDashboard.test.tsx` renders with a fixture user (no network).
- [x] Manual smoke on `/dashboard`.

## Notes

Start with `useCurrentUser.ts` — the loader and dashboard are mechanical follow-ons.
