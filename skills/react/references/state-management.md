# State Management Patterns

## Where to put state — ladder

1. **Local `useState`** — only one component reads/writes it.
2. **Lifted state** — two siblings share it; lift to their common parent.
3. **`useReducer`** — multiple actions mutate a related shape; transitions matter.
4. **Context + reducer** — many descendants need read or dispatch access.
5. **External store** (Zustand/Jotai/Redux) — many components across the tree subscribe with different selectors and re-render independently.
6. **Server cache** (React Query) — state that is fetched from a server; treat fetched data as cache, not local state.

Don't skip rungs. Most "we need Redux" turns out to be rung 1 or 2.

## Reducer shape

```ts
type State = { items: Item[]; selectedId: string | null };
type Action = { type: 'add'; item: Item } | { type: 'select'; id: string } | { type: 'remove'; id: string };

function reducer(s: State, a: Action): State {
  switch (a.type) {
    case 'add':
      return { ...s, items: [...s.items, a.item] };
    case 'select':
      return { ...s, selectedId: a.id };
    case 'remove':
      return { ...s, items: s.items.filter((i) => i.id !== a.id), selectedId: s.selectedId === a.id ? null : s.selectedId };
  }
}
```

## Immer for deep updates

Hand-rolling immutable updates of nested shapes is verbose and bug-prone. `useImmer` / `useImmerReducer` lets you write mutations on a draft.

```ts
const [state, update] = useImmer(initial);
update((d) => {
  d.users[0].profile.tags.push('admin');
});

const [s, dispatch] = useImmerReducer((d, a: Action) => {
  switch (a.type) {
    case 'add':
      d.items.push(a.item);
      break;
  }
}, initial);
```

Use when state has nested arrays/objects ≥2 levels deep. For flat state, plain `useReducer` is clearer.

## Anti-patterns

- Storing derived values in state. Compute in render (memoize only if expensive).
- Storing the same data in two stores (e.g. URL + local state) without a sync layer.
- A reducer that returns `state` unchanged for unknown actions silently — make it exhaustive (TS `never` check).
