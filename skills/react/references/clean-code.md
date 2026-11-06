# Clean Code Tips

## Element prop pattern

Accept a _React element_ as a prop instead of a bundle of config props.

```tsx
// hard to extend
<Page header={{ title, subtitle, breadcrumbs, actions }} />

// open to extension
<Page header={<PageHeader title={title} actions={<SaveButton />} />} />
```

Use when: a slot is open-ended and the parent shouldn't dictate its shape.

## Splitting context to avoid wasted re-renders

A context value re-render hits _every_ consumer, regardless of which field changed. Split contexts by _change frequency_ and _consumer set_.

Before (one mega-context):

```tsx
<AppContext.Provider value={{ user, theme, locale, cart, notifications }}>
```

After:

```tsx
<UserCtx.Provider value={user}>
  <ThemeCtx.Provider value={theme}>
    <CartCtx.Provider value={cart}>{children}</CartCtx.Provider>
  </ThemeCtx.Provider>
</UserCtx.Provider>
```

Or use a selector-based store (Zustand, Jotai, `use-context-selector`) when fields are interrelated.

Also: memoize the context value object if it's literal-constructed in render.

```tsx
const value = useMemo(() => ({ user, signOut }), [user, signOut]);
```
