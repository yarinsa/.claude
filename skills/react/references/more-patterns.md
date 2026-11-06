# Compound Components & Observer

## Compound components

Parent + children share implicit state via context. Consumers compose the parts; the parent coordinates them.

```tsx
<Tabs defaultValue="overview">
  <Tabs.List>
    <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
    <Tabs.Trigger value="logs">Logs</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Panel value="overview">...</Tabs.Panel>
  <Tabs.Panel value="logs">...</Tabs.Panel>
</Tabs>
```

Implementation:

- `Tabs` creates context with `{ value, setValue }`.
- `Tabs.Trigger` reads context, marks itself active, calls `setValue`.
- `Tabs.Panel` reads context and renders only when its `value` matches.

Use when: parts are _coupled but rearrangeable_. The consumer decides order, wrapping, and which subset to include.

## Observer pattern

A subject (store/event bus) notifies subscribers on change. In React, this is what `useSyncExternalStore` exists for — bridging an external mutable store into render-safe subscriptions.

```tsx
function useObservable<T>(subject: Subject<T>): T {
  return useSyncExternalStore(
    (cb) => subject.subscribe(cb),
    () => subject.getSnapshot(),
  );
}
```

Reach for it when:

- State lives outside React (websocket, BroadcastChannel, third-party store).
- Many components must react to one event without re-rendering an ancestor.
- A Redux-like store is overkill but global pub/sub is needed.
