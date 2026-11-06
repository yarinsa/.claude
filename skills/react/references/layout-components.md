# Layout Components

A layout component owns _positioning and spacing only_. It does not own data, business logic, or domain semantics.

## Patterns

### Split-screen / Splitter

Two-pane layout where each pane is a `children` slot. Take `leftWeight`/`rightWeight` (or `direction`) as props, not the content.

```tsx
<Split>
  <Sidebar />
  <Editor />
</Split>
```

Signal to extract: two pages repeat the same `flex` math around different content.

### List

A list component takes an `items` array plus an `ItemComponent` (or a render-prop / element-prop). The list owns iteration and key handling, not the row UI.

```tsx
<List items={users} render={(u) => <UserRow user={u} />} />
```

Variant: pass `itemKey: (item) => string` if `id` is not stable.

### Modal shell

A `Modal` is layout: overlay, focus trap, dismiss. The body is `children`. Do not bake form contents into the modal.

```tsx
<Modal isOpen onClose={close}>
  <ConfirmDelete onConfirm={...} />
</Modal>
```

## Signals you need a layout component

- Same JSX skeleton appears across 3+ pages.
- Pages diff only in their inner content.
- `className`/`style` props are being passed through 2+ levels.

## Anti-patterns

- Layout component that also fetches data. Split into container + layout.
- Layout component with domain-specific prop names (`userListProps`). Make it generic.
- Modal/Drawer that takes a `title` _and_ `subtitle` _and_ `actions` — those are slots, not props.
