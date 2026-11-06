# API Layer & Async Operations

## API client

One client module per backend. Centralize base URL, auth headers, error normalization. No `fetch()` calls scattered through components.

```ts
// shared/api/client.ts
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'content-type': 'application/json', ...authHeaders(), ...init?.headers },
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json() as Promise<T>;
}
```

## Modeling request states

Avoid `{ data, isLoading, error }` ad-hoc per call. Use a discriminated union or a small hook that returns one.

```ts
type AsyncState<T> = { status: 'idle' } | { status: 'loading' } | { status: 'success'; data: T } | { status: 'error'; error: Error };
```

Renders become exhaustive:

```tsx
switch (state.status) {
  case 'idle':
    return null;
  case 'loading':
    return <Spinner />;
  case 'error':
    return <ErrorBanner error={state.error} />;
  case 'success':
    return <List items={state.data} />;
}
```

## Abort on unmount / dep change

Every effect that fetches must abort.

```ts
useEffect(() => {
  const ctrl = new AbortController();
  api<User>(`/users/${id}`, { signal: ctrl.signal })
    .then((data) => setState({ status: 'success', data }))
    .catch((e) => {
      if (e.name !== 'AbortError') setState({ status: 'error', error: e });
    });
  return () => ctrl.abort();
}, [id]);
```

## Retries, timeouts, dedupe

Hand-rolling these is where bugs live. Prefer React Query / SWR once you need any of: dedupe, background refetch, retry, cache invalidation.
