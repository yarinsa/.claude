---
name: design-patterns-typescript
description: Catalog of the 22 classic GoF design patterns in TypeScript, organized like refactoring.guru (creational, structural, behavioral). Use when choosing, naming, implementing, or reviewing a design pattern in TypeScript code; when refactoring toward a pattern (switch-on-type, telescoping constructors, tangled dependencies, god objects); or when the user mentions a pattern by name (factory, builder, singleton, adapter, decorator, facade, proxy, observer, strategy, command, state, visitor, etc.).
---

# Design Patterns in TypeScript

Based on the catalog at [refactoring.guru/design-patterns/typescript](https://refactoring.guru/design-patterns/typescript). Examples here are original, short, and idiomatic TypeScript.

## How to use this skill

1. Identify the problem shape with the picker below.
2. Open only the matching reference file:
   - [references/creational.md](references/creational.md): how objects get created
   - [references/structural.md](references/structural.md): how objects and classes are composed
   - [references/behavioral.md](references/behavioral.md): how objects communicate and divide responsibility
3. Before applying a pattern, check its **TS shortcut**. Many patterns collapse to a function, a closure, or a union type in TypeScript. Prefer the lightest form that solves the problem.

## Pattern picker

| Symptom in the code | Pattern | Category |
|---|---|---|
| `new ConcreteX()` scattered everywhere; need to swap families of products together | Abstract Factory | Creational |
| Constructor with many optional params; step-by-step assembly | Builder | Creational |
| Superclass needs to create objects but subclasses decide the type | Factory Method | Creational |
| Need copies of configured objects without knowing their class | Prototype | Creational |
| Exactly one shared instance (config, connection pool) | Singleton | Creational |
| Third-party / legacy interface doesn't match yours | Adapter | Structural |
| Class hierarchy exploding across two dimensions (shape × renderer) | Bridge | Structural |
| Tree of items where leaves and groups are treated the same | Composite | Structural |
| Add behavior (logging, caching, retry) without subclassing | Decorator | Structural |
| Callers drowning in a complex subsystem's API | Facade | Structural |
| Millions of similar objects eating memory | Flyweight | Structural |
| Lazy init, access control, caching, or remote access in front of an object | Proxy | Structural |
| Request should pass through ordered handlers (middleware) | Chain of Responsibility | Behavioral |
| Need undo/redo, queueing, or logging of operations | Command | Behavioral |
| Traverse a custom collection without exposing internals | Iterator | Behavioral |
| Many components talking to each other directly (spaghetti) | Mediator | Behavioral |
| Snapshot and restore state | Memento | Behavioral |
| Other objects must react when something changes | Observer | Behavioral |
| Big `switch (this.state)` repeated across methods | State | Behavioral |
| Swappable algorithms selected at runtime | Strategy | Behavioral |
| Same algorithm skeleton, varying steps | Template Method | Behavioral |
| Add operations over a fixed set of node types (ASTs) | Visitor | Behavioral |

## Commonly confused pairs

- **Strategy vs State**: Strategy is chosen by the client and doesn't know other strategies. State objects transition the context themselves.
- **Decorator vs Proxy**: Same shape. Decorator adds behavior and is stacked by the client. Proxy controls access and usually manages the real object's lifecycle.
- **Adapter vs Facade**: Adapter makes one existing interface fit another expected interface. Facade defines a new, simpler interface over many objects.
- **Factory Method vs Abstract Factory**: Factory Method is one overridable creation method (inheritance). Abstract Factory is an object with several creation methods for a product family (composition).
- **Command vs Strategy**: Command packages *what* to do (and can be stored, undone). Strategy packages *how* to do the same thing.
- **Mediator vs Observer**: Mediator centralizes who talks to whom. Observer lets anyone subscribe dynamically. A mediator is often built on observer.

## TypeScript-specific guidance

- Use `interface` for pattern roles (Product, Handler, Strategy, Visitor). Structural typing means implementers don't need `implements`, but writing it documents intent and catches drift.
- Prefer **discriminated unions + exhaustive `switch`** over Visitor when the set of operations grows and the set of types is closed and owned by you.
- Prefer **plain functions / closures** over single-method classes (Strategy, Command, Template steps) unless the object needs state or identity.
- **ES modules are singletons.** A module-level `export const db = createDb()` usually beats a Singleton class. Inject it for testability.
- Use `private constructor` + `static` factory methods to force creation through a factory or builder.
- Use generators (`function*`, `[Symbol.iterator]`, `[Symbol.asyncIterator]`) for Iterator.
- Use `structuredClone` for deep copies in Prototype, but it drops class prototypes; implement `clone()` when identity of the class matters.
- Don't introduce a pattern for one implementation. Wait for the second variant (rule of three if unsure).

## Review checklist

When reviewing pattern usage, flag:
- A pattern whose abstraction has a single implementation and no planned second one.
- Singletons that hide dependencies and make tests share state.
- Visitor/double-dispatch where a union type would be simpler.
- Decorators/Proxies that don't forward the full interface (missing methods break substitutability).
- Observers that never unsubscribe (memory leaks in long-lived processes and UI).
