---
name: react
description: React patterns umbrella - component shape (compound, layout/list, container, partial application, recursive), plus catalogue of advanced patterns, performance, state, design-system and TypeScript practices. Invoke when authoring, refactoring or reviewing React/TypeScript components, when a component's shape is in question or accumulating configuration props, refactoring hooks/state, designing component APIs, or making React architecture decisions.
---

# React

Use this skill when the task involves:

- Designing a new React component API (props shape, controlled vs uncontrolled, composition vs configuration).
- Refactoring re-render hotspots, optimizing rendering paths, or deciding where memoization actually pays off.
- Picking a state-management approach (local state, reducer, context, react-query, immer).
- Authoring or reviewing custom hooks.
- Building/extending a design-system component.
- Improving TypeScript ergonomics on components, hooks, reducers, or context.

## How to use this skill

1. Identify which **category** the task falls into using the catalogue below.
2. Read the matching `references/<category>.md` for pattern names, intent, and when-to-apply signals.
3. If a pattern needs a worked example, look in `examples/`. If a deeper reference is needed, check the local cache (`.cache/extracted/<chapter>/<lecture>/`) — author's source code from the underlying course, available locally only.
4. Apply the pattern in the user's codebase using THEIR conventions — do not paste cached code verbatim into the repo.

## Catalogue

| Category                   | When to reach for it                                                                                                                                                                                                    | Reference                                                           |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Layout components          | Splitter/list/modal shells whose only job is arranging children. Stop passing `style` props around — pass the layout as a component.                                                                                    | [layout-components.md](references/layout-components.md)             |
| Container components       | A component fetching its own data has dual responsibility. Extract the data concern into a Loader/Container parent.                                                                                                     | [container-components.md](references/container-components.md)       |
| Controlled vs uncontrolled | Choosing where the source of truth lives for inputs, modals, popovers. Default uncontrolled; promote to controlled when a parent needs to read or override the value.                                                   | [controlled-uncontrolled.md](references/controlled-uncontrolled.md) |
| HOCs                       | Sharing cross-cutting concerns (auth/permission gating, data loading, mutation wrappers) by _wrapping_ rather than composing children. Modern code prefers hooks; reach for HOCs only when wrap-time injection matters. | [hocs.md](references/hocs.md)                                       |
| Custom hooks               | Reusable stateful logic that does not render. Default extraction unit once two components share state behavior.                                                                                                         | [custom-hooks.md](references/custom-hooks.md)                       |
| Functional patterns        | Recursive components, composition over inheritance, partial application of components.                                                                                                                                  | [functional-patterns.md](references/functional-patterns.md)         |
| More patterns              | Compound components, observer pattern in React.                                                                                                                                                                         | [more-patterns.md](references/more-patterns.md)                     |
| Advanced concepts          | Portals, error boundaries, key semantics, refs, forwardRef, hydration mismatches, lazy boundaries.                                                                                                                      | [advanced-concepts.md](references/advanced-concepts.md)             |
| Clean code                 | Element-prop pattern, splitting context to avoid unnecessary re-renders.                                                                                                                                                | [clean-code.md](references/clean-code.md)                           |
| Scalable architecture      | Route components, encapsulation boundaries, where domain logic lives.                                                                                                                                                   | [architecture.md](references/architecture.md)                       |
| API layer                  | API client abstraction; modeling loading/error/success states; aborting in-flight requests.                                                                                                                             | [api-layer.md](references/api-layer.md)                             |
| React Query                | When to drop hand-rolled loaders for `useQuery`/`useMutation`; cache key design; invalidation.                                                                                                                          | [react-query.md](references/react-query.md)                         |
| State management           | Reducer-shaped state, `useImmer` / `useImmerReducer` for deep updates.                                                                                                                                                  | [state-management.md](references/state-management.md)               |
| Performance                | Code splitting, `useCallback`/`useMemo` discipline (only when referential identity is consumed downstream), `React.memo`, list virtualization, profiling first.                                                         | [performance.md](references/performance.md)                         |
| Design system              | Token foundations, extensible primitives, spacing/layer patterns, encapsulating styles.                                                                                                                                 | [design-system.md](references/design-system.md)                     |
| Advanced TypeScript        | Typing hooks, reducers, context, generics, generic components, type helpers, polymorphic & variant props.                                                                                                               | [typescript.md](references/typescript.md)                           |

## Decision rules (apply in order)

1. **Smallest change wins.** If a local refactor solves it, do not introduce a pattern.
2. **Prove the problem before applying memoization or HOCs.** Profile first. Identity-based optimizations only help if a downstream consumer compares by identity.
3. **Prefer composition over configuration.** A `prop` taking 7 booleans is a signal to expose slots/children instead.
4. **Co-locate state with its only consumer.** Lift only when a second consumer appears, not preemptively.
5. **Type at the boundary, infer in the middle.** Annotate exported component props and hook returns; let TS infer internals.
6. **Do not invent abstractions for hypothetical future requirements** — see CLAUDE.md "Simplicity First".

## Anti-patterns to flag during review

- `useCallback`/`useMemo` wrapping values that no memoized consumer reads.
- Context whose value object is reconstructed every render → forces all consumers to re-render. Split context or memoize the value.
- HOC chains 3+ deep — usually a custom hook would be clearer.
- Effects that exist only to sync derived state — derive in render instead.
- Controlled inputs whose owner never reads the value — should be uncontrolled.
- Props that are actually configuration of an internal child — pass the child as `children` or an element prop.
- `any` in TS (per repo rule). Reach for generics, `unknown`, or discriminated unions instead.
- A shared component or hook whose options enumerate every caller's differences (`ListPageLayout` with eight config props) is the duplication moved, not removed. Dedup only when the copies differ in content the caller can compose, not in configuration.

## Local references (not committed)

The author's original course source is cached at `.cache/extracted/<chapter-slug>/<lecture-slug>/` under this skill directory. Each lecture typically ships a `codes-before/` and `codes-after/` pair. Use these for deeper reading when a reference file is not enough, but **never copy them verbatim into a user repo** — translate the pattern into the project's conventions.

Run `scripts/validate.sh` to confirm the cache is present.

---

## Component shape patterns

Minimal runnable examples live in `examples/<pattern>/`. Read the relevant folder before writing the component - the examples are the spec for the shape.

### Pattern selection

| Symptom                                                                                                                   | Pattern                               | Reference                                       |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------- |
| Primitive keeps growing props to describe its own content (`title`, `meta`, `headerAction`, `footer`, `contentClassName`) | **Compound components**               | `examples/compound-components/`                 |
| Same list chrome (spacing, numbering, separators) repeated with different row content                                     | **Layout / list components**          | `examples/layout-components/`                   |
| Presentational component fetches its own data, so it can't be tested or reused                                            | **Container components**              | `examples/container-components/`                |
| Several components differ only by a fixed prop value                                                                      | **Partial application / composition** | `examples/functional-programming/`              |
| Rendering arbitrarily nested data                                                                                         | **Recursive component**               | `examples/functional-programming/recursive.jsx` |

### Compound components

Root owns the surface and the state, publishes both via context; sub-components attached as statics (`Pane.Header`, `Pane.Body`). Callers compose the content; the primitive decides nothing about what goes inside.

```jsx
<Pane collapsible defaultOpen>
  <Pane.Header>
    <Pane.Title>Details</Pane.Title>
    <Pane.Action>
      <Button />
    </Pane.Action>
  </Pane.Header>
  <Pane.Body>{grid}</Pane.Body>
</Pane>
```

Rules:

- Sub-components read the root context and throw a named error when rendered outside it. No silent no-op.
- Behavior branches (collapsible vs static, loading vs loaded) live inside the primitive and are read from context - caller JSX stays identical either way.
- When a sub-component must render outside an interactive wrapper (e.g. an action button that would otherwise nest inside a trigger `<button>`), partition children by `child.type === SubComponent` in the parent sub-component. Nested interactive elements are invalid DOM and swallow clicks.
- Context value is derived, not duplicated - never mirror an open/selected prop into extra state.

### Layout / list components

The list owns the chrome and takes the row component as a prop; rows own their own markup and know nothing about the container.

```jsx
<RegularList items={authors} sourceName="author" ItemComponent={SmallAuthorListItem} />
<NumberedList items={books} sourceName="book" ItemComponent={LargeBookListItem} />
```

Rules:

- Pass a component (`ItemComponent`), not a render callback, when the row is a stable component - it keeps the item's own memoization and DevTools name.
- `sourceName` maps the item onto the row's prop name; skip it when rows read from context instead.
- A descriptor array (`{ key, Component }[]`) is the same pattern for heterogeneous children - it lets callers declare sections as data.

### Container components

The container fetches; the children render. Reference examples inject via `React.Children.map` + `cloneElement`; prefer a **context** in TypeScript codebases - `cloneElement` loses type safety on the injected props and breaks the moment a child is wrapped.

```jsx
<ResourceLoader resourceUrl="/users/1" resourceName="user">
  <UserInfo />
</ResourceLoader>
```

Rules:

- One container per drawer/page/section owns every fetch for that scope; panes and rows fetch nothing.
- Render nothing until the entity resolves - that removes the null guard from every child and makes the injected value non-nullable.
- The container is the only place that reads route params / outlet context; children take data from the hook.

### Partial application and composition

Specialize by pre-applying props, not by copying a wrapper component per variant.

```jsx
export const partial = (Component, partialProps) => (props) => <Component {...partialProps} {...props} />;

export const SmallButton = partial(Button, { size: 'small' });
export const LargeRedButton = partial(Button, { size: 'large', color: 'crimson' });
```

Rules:

- Caller props must win over the pre-applied ones (spread `props` last).
- Set `displayName` on the returned component so DevTools and error boundaries stay readable.
- In TypeScript, type it `FunctionComponent<Omit<P, K>>` so `displayName` assignment is legal and the pre-applied props disappear from the public type.
- Composition (`SmallButton` wrapping `Button`) is the same idea written by hand - use it when the variant also adds markup, `partial` when it only fixes props.

### Recursive components

A component that renders itself for nested data, with the scalar case as the base case (`examples/functional-programming/recursive.jsx`). Always key the recursive children, and cap depth or trust the data shape - unbounded recursion on a cyclic graph hangs the render.

### Anti-patterns

- Prop-soup primitives: config props describing content the caller could have composed.
- Presentational components reaching into router/outlet/query hooks.
- A wrapper component whose whole body is `<Base {...props} fixed="value" />` (use `partial`).
- Copying the list container to change row markup, or copying the row to change container chrome.
