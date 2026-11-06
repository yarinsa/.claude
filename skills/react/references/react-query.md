# React Query

Use it when any of these are true: dedupe in-flight requests, background refetch, retry policy, cache invalidation, optimistic updates, paginated/infinite lists, request-aware Suspense.

## Cache keys

Keys are arrays. First element is a stable namespace; subsequent elements are parameters.

```ts
useQuery({ queryKey: ['users', userId], queryFn: () => fetchUser(userId) });
useQuery({ queryKey: ['users', 'list', filters], queryFn: () => fetchUsers(filters) });
```

Rule: anything that changes the _response_ must be in the key.

## Mutations + invalidation

```ts
const qc = useQueryClient();
const update = useMutation({
  mutationFn: updateUser,
  onSuccess: (_, vars) => {
    qc.invalidateQueries({ queryKey: ['users', vars.id] });
    qc.invalidateQueries({ queryKey: ['users', 'list'] });
  },
});
```

Prefer `invalidateQueries` (refetch on next access) over `setQueryData` unless you have the full new shape and want to skip a round-trip.

## Optimistic updates

```ts
const toggle = useMutation({
  mutationFn: toggleStar,
  onMutate: async (id) => {
    await qc.cancelQueries({ queryKey: ['item', id] });
    const prev = qc.getQueryData<Item>(['item', id]);
    qc.setQueryData<Item>(['item', id], (o) => o && { ...o, starred: !o.starred });
    return { prev };
  },
  onError: (_e, id, ctx) => ctx?.prev && qc.setQueryData(['item', id], ctx.prev),
  onSettled: (_d, _e, id) => qc.invalidateQueries({ queryKey: ['item', id] }),
});
```

## Configuration defaults to consider

- `staleTime`: 0 thrashes the network. Set to seconds–minutes depending on data freshness needs.
- `gcTime`: how long unused cache lingers.
- `retry`: pick 0 for mutations, default `3` for reads.
- `refetchOnWindowFocus`: turn off for noisy desktops.

## Anti-patterns

- Wrapping every fetch in `useEffect` instead of `useQuery`.
- Using `data` without checking `isSuccess` / `isLoading` — `data` is `undefined` at first.
- Putting derived UI state in the query cache; keep that in component state.
- Re-creating the `queryClient` per render.
