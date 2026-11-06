# Advanced TypeScript for React

## Typing hooks

### `useState`

Type the value when the initial value is ambiguous (`null`, `[]`, `undefined`).

```ts
const [user, setUser] = useState<User | null>(null);
const [items, setItems] = useState<Item[]>([]);
```

### `useReducer`

Type state and the action union; let TS infer the reducer return.

```ts
type State = { items: Item[] };
type Action = { type: 'add'; item: Item } | { type: 'clear' };
const [s, dispatch] = useReducer<Reducer<State, Action>>(reducer, { items: [] });
```

### `useRef`

```ts
const inputRef = useRef<HTMLInputElement>(null); // for DOM nodes (read-only ref)
const counter = useRef<number>(0); // mutable instance value
```

### Custom hook returns

Return a tuple for `[value, set]` shapes; an object otherwise. Annotate the return type when it's part of the public API.

```ts
export function useDisclosure(): { isOpen: boolean; open: () => void; close: () => void; toggle: () => void } { ... }
```

## Typing context

```ts
const UserCtx = createContext<User | null>(null);

export function useUser(): User {
  const u = useContext(UserCtx);
  if (!u) throw new Error('useUser must be used inside <UserProvider>');
  return u;
}
```

The hook narrows away `null` so consumers never deal with it.

## Generics on components

```tsx
type ListProps<T> = {
  items: T[];
  render: (item: T) => ReactNode;
  itemKey: (item: T) => string;
};

function List<T>({ items, render, itemKey }: ListProps<T>) {
  return (
    <ul>
      {items.map((i) => (
        <li key={itemKey(i)}>{render(i)}</li>
      ))}
    </ul>
  );
}
```

Inference flows from `items` to `render`/`itemKey`.

## Type helpers

```ts
// Make some keys required (inverse of Partial<Pick<T, K>>)
type RequireKeys<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Distinguish discriminated unions
type Discriminate<T, K extends keyof T, V extends T[K]> = T extends { [P in K]: V } ? T : never;

// `as const` to lock literal types
const VARIANTS = ['primary', 'secondary', 'danger'] as const;
type Variant = (typeof VARIANTS)[number]; // 'primary' | 'secondary' | 'danger'
```

## Variant / differentiating props

Discriminated unions are the cleanest way to express "if X, then Y is required":

```ts
type ButtonProps = { variant: 'link'; href: string; onClick?: never } | { variant: 'button'; href?: never; onClick: () => void };
```

## Polymorphic components

```ts
type AsProp<C extends ElementType> = { as?: C };
type PolymorphicProps<C extends ElementType, P = {}> =
  P & AsProp<C> & Omit<ComponentPropsWithoutRef<C>, keyof P | 'as'>;

function Box<C extends ElementType = 'div'>({ as, ...rest }: PolymorphicProps<C, { padding?: 'sm' | 'md' }>) {
  const Tag = as ?? 'div';
  return <Tag {...rest} />;
}
```

`forwardRef` + polymorphism gets fiddly; the Radix `Slot` pattern is often simpler.

## Empty object & requiring props

- `{}` matches _anything non-null_. Use `Record<string, never>` for "object with no keys", or just `Record<string, unknown>` for "any object".
- Required props: declare without `?` and without a default.

## Repo rule

No `any`. Use `unknown` at boundaries, narrow with type guards, or reach for generics/discriminated unions.
