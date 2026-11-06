# Scalable Project Architecture

## Folder shape

Organize by _feature_, not by _file type_. Components, hooks, types, and tests for a feature live together.

```
src/
  features/
    users/
      UserList.tsx
      UserCard.tsx
      useUsers.ts
      api.ts
      types.ts
      __tests__/
    billing/
  shared/
    ui/         # design-system primitives
    hooks/
    lib/
  routes/       # route components only — thin
  app/          # providers, root layout
```

## Route components are thin

A route component does three things:

1. Read params/query.
2. Compose feature containers.
3. Set page chrome (title, breadcrumbs).

No business logic, no inline fetching, no styling beyond layout slots.

## Encapsulation boundaries

A feature exposes a small `index.ts` barrel. Cross-feature imports go through it; deep imports into another feature's internals are a code smell.

```ts
// features/users/index.ts
export { UserList } from './UserList';
export { useCurrentUser } from './useCurrentUser';
export type { User } from './types';
```

## Shared vs feature

Move code into `shared/` only when ≥2 features use it. Premature sharing creates god modules.

## Domain logic placement

| Logic kind                  | Lives in                                   |
| --------------------------- | ------------------------------------------ |
| HTTP / GraphQL calls        | `features/<x>/api.ts`                      |
| Data shaping for UI         | a feature hook (`useUsers`)                |
| Pure transforms             | `features/<x>/lib.ts` (testable, no React) |
| Cross-cutting (auth, theme) | `app/providers/` + `shared/hooks/`         |
