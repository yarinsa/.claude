# Controlled vs Uncontrolled

The choice is about _where the source of truth lives_: in the component (uncontrolled) or in the parent (controlled).

## Default: uncontrolled

Component owns its own state. Parent receives the final value via callback (`onChange`, `onSubmit`) or a ref.

```tsx
function NameInput({ defaultValue = '', onSubmit }: { defaultValue?: string; onSubmit: (v: string) => void }) {
  const [value, setValue] = useState(defaultValue);
  return <input value={value} onChange={(e) => setValue(e.target.value)} onBlur={() => onSubmit(value)} />;
}
```

Simpler API. Parent doesn't re-render on every keystroke.

## Promote to controlled when

- A sibling needs to read or react to the value.
- Parent must be able to _override_ the value (reset, programmatic set).
- The value participates in URL/query-param state.
- Two inputs must stay in sync.

```tsx
function NameInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <input value={value} onChange={(e) => onChange(e.target.value)} />;
}
```

## Hybrid (controllable) components

Accept both `value`/`onChange` _and_ `defaultValue`. Choose the mode based on which is present.

```tsx
function useControllable<T>(controlled: T | undefined, defaultValue: T) {
  const [internal, setInternal] = useState(defaultValue);
  const isControlled = controlled !== undefined;
  const value = isControlled ? controlled : internal;
  const set = isControlled ? () => {} : setInternal;
  return [value, set] as const;
}
```

Same pattern works for `<Modal isOpen?>`, `<Tabs value?>`, `<Disclosure open?>`.

## Anti-patterns

- Controlled input whose owner only reads the value on submit — it should be uncontrolled with a ref or `onSubmit`.
- Switching between controlled and uncontrolled at runtime — React warns and behavior is undefined.
- Storing the same value in both component state and URL — pick one source of truth.
