# Container Components

A container component owns _data fetching and shape transformation_, then renders a child purely from props. The child stays presentational and easy to test.

## Pattern

```tsx
function UserLoader({ id, children }: { id: string; children: (u: User) => ReactNode }) {
  const { data, error, isLoading } = useUser(id);
  if (isLoading) return <Spinner />;
  if (error) return <ErrorBanner error={error} />;
  return <>{children(data)}</>;
}

// usage
<UserLoader id={userId}>{(user) => <UserCard user={user} />}</UserLoader>;
```

## When to use

- A presentational component is being passed the _same_ fetched data in many call sites — wrap it once.
- Loading/error UI is repeated.
- A test wants to render the presentational component with a fixture; the container forces that separation.

## When NOT to use

- The data is consumed by exactly one component → just call the hook inside it.
- React Query is already in use → its `useQuery` + `Suspense` boundary is the container.

## Variants

- **Current-user loader** — a thin wrapper around an auth/session hook that exposes the user to any child.
- **Resource loader** — generic over resource type; pair with a typed `useResource<T>` hook.

## Anti-patterns

- Container that _also_ renders nontrivial presentational UI. Split them.
- Container exposing `data | undefined` to children — handle the loading state inside the container, render children only on success.
