# Behavioral Patterns

Algorithms and the assignment of responsibilities between objects.
Source: [refactoring.guru/design-patterns/behavioral-patterns](https://refactoring.guru/design-patterns/behavioral-patterns)

- [Chain of Responsibility](#chain-of-responsibility)
- [Command](#command)
- [Iterator](#iterator)
- [Mediator](#mediator)
- [Memento](#memento)
- [Observer](#observer)
- [State](#state)
- [Strategy](#strategy)
- [Template Method](#template-method)
- [Visitor](#visitor)

---

## Chain of Responsibility

[refactoring.guru](https://refactoring.guru/design-patterns/chain-of-responsibility/typescript/example)

**Intent:** Pass a request along a chain of handlers. Each handler either processes it or passes it to the next.

**Use when:** several handlers may process a request in a sequence determined at runtime (middleware, validation pipelines, event bubbling, support escalation).

```ts
interface Request { user?: { role: string }; path: string; }
type Next = () => Promise<Response>;
type Handler = (req: Request, next: Next) => Promise<Response>;

const auth: Handler = async (req, next) =>
  req.user ? next() : new Response("Unauthorized", { status: 401 });

const adminOnly: Handler = async (req, next) =>
  req.path.startsWith("/admin") && req.user?.role !== "admin"
    ? new Response("Forbidden", { status: 403 })
    : next();

function chain(handlers: Handler[], final: (req: Request) => Promise<Response>) {
  return (req: Request): Promise<Response> => {
    const run = (i: number): Promise<Response> =>
      i < handlers.length ? handlers[i](req, () => run(i + 1)) : final(req);
    return run(0);
  };
}

const handle = chain([auth, adminOnly], async () => new Response("OK"));
```

**Pitfalls:** a request can fall off the end unhandled; always define a terminal handler.

---

## Command

[refactoring.guru](https://refactoring.guru/design-patterns/command/typescript/example)

**Intent:** Turn a request into a standalone object containing all information about it, so you can parameterize, queue, log, and undo operations.

```ts
interface Command {
  execute(): void;
  undo(): void;
}

class Editor { text = ""; }

class InsertText implements Command {
  constructor(private editor: Editor, private at: number, private value: string) {}
  execute() {
    const t = this.editor.text;
    this.editor.text = t.slice(0, this.at) + this.value + t.slice(this.at);
  }
  undo() {
    const t = this.editor.text;
    this.editor.text = t.slice(0, this.at) + t.slice(this.at + this.value.length);
  }
}

class History {
  private done: Command[] = [];
  private undone: Command[] = [];
  run(cmd: Command) { cmd.execute(); this.done.push(cmd); this.undone = []; }
  undo() { const c = this.done.pop(); if (c) { c.undo(); this.undone.push(c); } }
  redo() { const c = this.undone.pop(); if (c) { c.execute(); this.done.push(c); } }
}
```

**TS shortcut:** without undo, a command is just a closure `() => void`. For serializable commands (queues, event sourcing), use a discriminated union of plain data objects plus a dispatcher.

**Pitfalls:** undo needs enough captured state to reverse the operation; many tiny command classes.

---

## Iterator

[refactoring.guru](https://refactoring.guru/design-patterns/iterator/typescript/example)

**Intent:** Traverse elements of a collection without exposing its underlying representation (list, tree, graph, paginated API).

```ts
class TreeNode<T> {
  children: TreeNode<T>[] = [];
  constructor(public value: T) {}

  // depth-first by default
  *[Symbol.iterator](): IterableIterator<T> {
    yield this.value;
    for (const c of this.children) yield* c;
  }

  *breadthFirst(): IterableIterator<T> {
    const queue: TreeNode<T>[] = [this];
    while (queue.length) {
      const n = queue.shift()!;
      yield n.value;
      queue.push(...n.children);
    }
  }
}

for (const v of tree) { /* ... */ }
const values = [...tree.breadthFirst()];

// Async iterator over a paginated API
async function* allUsers(fetchPage: (cursor?: string) => Promise<{ items: User[]; next?: string }>) {
  let cursor: string | undefined;
  do {
    const page = await fetchPage(cursor);
    yield* page.items;
    cursor = page.next;
  } while (cursor);
}
```

**TS shortcut:** generators are the iterator pattern built into the language. Write explicit `next()` classes only when you need extra methods like `reset()` or `peek()`.

**Pitfalls:** mutating the collection while iterating.

---

## Mediator

[refactoring.guru](https://refactoring.guru/design-patterns/mediator/typescript/example)

**Intent:** Reduce chaotic dependencies between objects by restricting direct communication and forcing them to collaborate through a mediator.

**Use when:** components are hard to reuse because they reference many others directly (form fields toggling each other, chat participants, air-traffic control).

```ts
type Event = "loginToggled" | "submitClicked";

interface Mediator { notify(sender: Component, event: Event): void; }

abstract class Component {
  constructor(protected mediator?: Mediator) {}
}

class Checkbox extends Component {
  checked = false;
  toggle() { this.checked = !this.checked; this.mediator?.notify(this, "loginToggled"); }
}
class TextField extends Component { visible = true; value = ""; }
class Button extends Component {
  click() { this.mediator?.notify(this, "submitClicked"); }
}

class AuthDialog implements Mediator {
  readonly hasAccount = new Checkbox(this);
  readonly email = new TextField(this);
  readonly confirmPassword = new TextField(this);
  readonly submit = new Button(this);

  notify(_sender: Component, event: Event) {
    if (event === "loginToggled") this.confirmPassword.visible = !this.hasAccount.checked;
    if (event === "submitClicked") { /* validate fields, call API */ }
  }
}
```

**Pitfalls:** the mediator can turn into a god object; split by feature.

---

## Memento

[refactoring.guru](https://refactoring.guru/design-patterns/memento/typescript/example)

**Intent:** Save and restore the previous state of an object without revealing the details of its implementation.

```ts
class Memento {
  // opaque to everyone except the originator
  constructor(readonly state: Readonly<{ text: string; cursor: number }>, readonly at = Date.now()) {}
}

class Editor {
  private text = "";
  private cursor = 0;

  type(s: string) { this.text += s; this.cursor = this.text.length; }

  save(): Memento { return new Memento({ text: this.text, cursor: this.cursor }); }
  restore(m: Memento) { ({ text: this.text, cursor: this.cursor } = m.state); }
}

class Caretaker {
  private history: Memento[] = [];
  constructor(private editor: Editor) {}
  backup() { this.history.push(this.editor.save()); }
  undo() { const m = this.history.pop(); if (m) this.editor.restore(m); }
}
```

**TS shortcut:** with immutable state (Redux-style), every previous state object *is* a memento; keep an array of them.

**Pitfalls:** RAM cost of many snapshots; consider diffs or a size cap. TypeScript `private` is compile-time only; use `#private` fields if encapsulation must hold at runtime.

---

## Observer

[refactoring.guru](https://refactoring.guru/design-patterns/observer/typescript/example)

**Intent:** Define a subscription mechanism to notify multiple objects about events happening to the object they observe.

```ts
type Listener<T> = (payload: T) => void;

class Emitter<Events extends Record<string, unknown>> {
  private listeners: { [K in keyof Events]?: Set<Listener<Events[K]>> } = {};

  on<K extends keyof Events>(event: K, fn: Listener<Events[K]>): () => void {
    (this.listeners[event] ??= new Set()).add(fn);
    return () => this.listeners[event]?.delete(fn); // unsubscribe handle
  }

  emit<K extends keyof Events>(event: K, payload: Events[K]) {
    this.listeners[event]?.forEach((fn) => fn(payload));
  }
}

const store = new Emitter<{ priceChanged: { sku: string; price: number } }>();
const off = store.on("priceChanged", ({ sku, price }) => console.log(sku, price));
store.emit("priceChanged", { sku: "A1", price: 9.99 });
off();
```

**TS shortcut:** in the browser and Node, `EventTarget` / `EventEmitter` are built-in observers; RxJS Observables and signals are richer forms.

**Pitfalls:** forgotten subscriptions leak memory; notification order is not guaranteed by design; cascading updates can be hard to trace.

---

## State

[refactoring.guru](https://refactoring.guru/design-patterns/state/typescript/example)

**Intent:** Let an object alter its behavior when its internal state changes. It appears as if the object changed its class.

**Use when:** behavior depends on state and the class has big conditionals on the current state repeated across many methods.

```ts
interface OrderState {
  pay(order: Order): void;
  ship(order: Order): void;
  cancel(order: Order): void;
}

class Order {
  constructor(public state: OrderState = new Pending()) {}
  pay() { this.state.pay(this); }
  ship() { this.state.ship(this); }
  cancel() { this.state.cancel(this); }
}

const invalid = (action: string, state: string) => { throw new Error(`Cannot ${action} when ${state}`); };

class Pending implements OrderState {
  pay(o: Order) { o.state = new Paid(); }
  ship() { invalid("ship", "pending"); }
  cancel(o: Order) { o.state = new Cancelled(); }
}
class Paid implements OrderState {
  pay() { invalid("pay", "paid"); }
  ship(o: Order) { o.state = new Shipped(); }
  cancel(o: Order) { /* refund */ o.state = new Cancelled(); }
}
class Shipped implements OrderState {
  pay() { invalid("pay", "shipped"); }
  ship() { invalid("ship", "shipped"); }
  cancel() { invalid("cancel", "shipped"); }
}
class Cancelled implements OrderState {
  pay() { invalid("pay", "cancelled"); }
  ship() { invalid("ship", "cancelled"); }
  cancel() {}
}
```

**TS shortcut:** for few states with little behavior, a discriminated union plus a transition table (`Record<State, Partial<Record<Action, State>>>`) is simpler and serializable. Libraries like XState formalize this.

**Pitfalls:** overkill for 2-3 states with trivial transitions.

---

## Strategy

[refactoring.guru](https://refactoring.guru/design-patterns/strategy/typescript/example)

**Intent:** Define a family of algorithms, put each in its own class, and make them interchangeable.

**Use when:** you have variants of an algorithm selected at runtime, or a big conditional choosing between them.

```ts
interface ShippingStrategy {
  cost(weightKg: number, distanceKm: number): number;
}

const strategies = {
  standard: { cost: (w, d) => 5 + w * 0.5 + d * 0.01 },
  express:  { cost: (w, d) => 15 + w * 1.0 + d * 0.02 },
  pickup:   { cost: () => 0 },
} satisfies Record<string, ShippingStrategy>;

type ShippingMethod = keyof typeof strategies;

class Checkout {
  constructor(private strategy: ShippingStrategy) {}
  setStrategy(s: ShippingStrategy) { this.strategy = s; }
  total(subtotal: number, w: number, d: number) { return subtotal + this.strategy.cost(w, d); }
}

new Checkout(strategies["express"]).total(100, 2, 300);
```

**TS shortcut:** a strategy is often just a function type: `type Comparator<T> = (a: T, b: T) => number`. Use objects when a strategy has several related methods or configuration.

**Pitfalls:** clients must know the differences between strategies to pick one.

---

## Template Method

[refactoring.guru](https://refactoring.guru/design-patterns/template-method/typescript/example)

**Intent:** Define the skeleton of an algorithm in a superclass and let subclasses override specific steps without changing its structure.

```ts
abstract class DataImporter<Row> {
  // the template method: fixed sequence
  async run(source: string): Promise<number> {
    const raw = await this.read(source);
    const rows = this.parse(raw);
    const valid = rows.filter((r) => this.validate(r));
    await this.save(valid);
    this.afterImport?.(valid.length); // optional hook
    return valid.length;
  }

  protected abstract parse(raw: string): Row[];
  protected abstract save(rows: Row[]): Promise<void>;

  // default implementations subclasses may override
  protected async read(source: string) { return (await fetch(source)).text(); }
  protected validate(_row: Row) { return true; }
  protected afterImport?(count: number): void;
}

class CsvUserImporter extends DataImporter<{ email: string }> {
  protected parse(raw: string) { return raw.split("\n").slice(1).map((l) => ({ email: l.trim() })); }
  protected override validate(r: { email: string }) { return r.email.includes("@"); }
  protected async save(rows: { email: string }[]) { /* db.insert(rows) */ }
}
```

**TS shortcut:** composition alternative: a function that takes the steps as parameters, `runImport({ read, parse, validate, save })`. Prefer it when you don't otherwise need a class hierarchy.

**Pitfalls:** inheritance-based; subclasses can break the skeleton's assumptions (Liskov). More steps = harder to maintain.

---

## Visitor

[refactoring.guru](https://refactoring.guru/design-patterns/visitor/typescript/example)

**Intent:** Separate algorithms from the objects on which they operate, so new operations can be added without changing the element classes.

**Use when:** you need many unrelated operations over a stable set of element types (AST nodes, document elements) and don't want to pollute those classes.

```ts
interface Visitor<R> {
  visitNumber(n: NumberLit): R;
  visitAdd(n: Add): R;
}

interface Expr { accept<R>(v: Visitor<R>): R; }

class NumberLit implements Expr {
  constructor(readonly value: number) {}
  accept<R>(v: Visitor<R>) { return v.visitNumber(this); }
}
class Add implements Expr {
  constructor(readonly left: Expr, readonly right: Expr) {}
  accept<R>(v: Visitor<R>) { return v.visitAdd(this); }
}

const evaluate: Visitor<number> = {
  visitNumber: (n) => n.value,
  visitAdd: (n) => n.left.accept(evaluate) + n.right.accept(evaluate),
};
const print: Visitor<string> = {
  visitNumber: (n) => String(n.value),
  visitAdd: (n) => `(${n.left.accept(print)} + ${n.right.accept(print)})`,
};

const expr = new Add(new NumberLit(1), new Add(new NumberLit(2), new NumberLit(3)));
expr.accept(evaluate); // 6
expr.accept(print);    // "(1 + (2 + 3))"
```

**TS shortcut (often better):** discriminated unions with an exhaustive `switch` give the same "add operations without touching types" benefit with less ceremony, and the compiler flags missing cases:

```ts
type Expr = { kind: "num"; value: number } | { kind: "add"; left: Expr; right: Expr };

function evaluate(e: Expr): number {
  switch (e.kind) {
    case "num": return e.value;
    case "add": return evaluate(e.left) + evaluate(e.right);
    default: { const _exhaustive: never = e; return _exhaustive; }
  }
}
```

**Pitfalls:** adding a new element type requires updating every visitor; visitors may need access to private fields of elements.
