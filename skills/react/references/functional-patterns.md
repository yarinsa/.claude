# Functional Patterns in React

## Recursive components

When the data is recursive (trees, comments-with-replies, nested menus), the component renders itself for children.

```tsx
function TreeNode({ node }: { node: Node }) {
  return (
    <li>
      {node.label}
      {node.children?.length ? (
        <ul>
          {node.children.map((c) => (
            <TreeNode key={c.id} node={c} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}
```

Watch for:

- Stable keys (use ids, not array index).
- Depth limits to avoid runaway renders on malformed data.
- Memoize the row component if subtrees are large and frequently re-rendered.

## Composition (children > props)

Pass _components_ as children/slots instead of describing them via props.

Bad:

```tsx
<Card title="..." subtitle="..." actions={[{ label, onClick }]} footer="..." />
```

Better:

```tsx
<Card>
  <Card.Header>...</Card.Header>
  <Card.Body>...</Card.Body>
  <Card.Footer>
    <Button>Save</Button>
  </Card.Footer>
</Card>
```

Each slot is independently overridable; consumers don't fight a config surface.

## Partial application of components

Pre-bind some props to get a specialized component.

```tsx
const PrimaryButton = (props: ButtonProps) => <Button variant="primary" {...props} />;
const DangerButton = (props: ButtonProps) => <Button variant="danger" {...props} />;
```

Or with a helper:

```tsx
const withDefaults =
  <P extends object>(C: ComponentType<P>, defaults: Partial<P>) =>
  (props: P) => <C {...defaults} {...props} />;
```

Use for: pre-themed variants, locale-bound widgets, table-cell renderers with fixed columns.
