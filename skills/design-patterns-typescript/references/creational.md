# Creational Patterns

Object-creation mechanisms that increase flexibility and reuse of existing code.
Source: [refactoring.guru/design-patterns/creational-patterns](https://refactoring.guru/design-patterns/creational-patterns)

- [Factory Method](#factory-method)
- [Abstract Factory](#abstract-factory)
- [Builder](#builder)
- [Prototype](#prototype)
- [Singleton](#singleton)

---

## Factory Method

[refactoring.guru](https://refactoring.guru/design-patterns/factory-method/typescript/example)

**Intent:** Define an interface for creating an object in a superclass, but let subclasses decide which class to instantiate.

**Use when:** a base class contains logic that works with a product, but the concrete product type varies per subclass; or you want users of a framework to extend its internal components.

```ts
interface Transport {
  deliver(cargo: string): string;
}

class Truck implements Transport {
  deliver(cargo: string) { return `Truck delivers ${cargo} by road`; }
}
class Ship implements Transport {
  deliver(cargo: string) { return `Ship delivers ${cargo} by sea`; }
}

abstract class Logistics {
  protected abstract createTransport(): Transport; // the factory method

  planDelivery(cargo: string): string {
    const t = this.createTransport();          // business logic is product-agnostic
    return t.deliver(cargo);
  }
}

class RoadLogistics extends Logistics {
  protected createTransport() { return new Truck(); }
}
class SeaLogistics extends Logistics {
  protected createTransport() { return new Ship(); }
}

new SeaLogistics().planDelivery("containers");
```

**TS shortcut:** if there's no surrounding base-class logic, pass a factory function instead: `planDelivery(cargo, create: () => Transport)`.

**Pitfalls:** a parallel subclass per product type can bloat the hierarchy.

---

## Abstract Factory

[refactoring.guru](https://refactoring.guru/design-patterns/abstract-factory/typescript/example)

**Intent:** Produce families of related objects without specifying their concrete classes.

**Use when:** code must work with several families of related products (e.g. UI widgets per OS theme) and products from different families must never be mixed.

```ts
interface Button { render(): string; }
interface Checkbox { render(): string; }

interface UIFactory {
  createButton(): Button;
  createCheckbox(): Checkbox;
}

const lightTheme: UIFactory = {
  createButton: () => ({ render: () => "<button class=light>" }),
  createCheckbox: () => ({ render: () => "<input class=light type=checkbox>" }),
};

const darkTheme: UIFactory = {
  createButton: () => ({ render: () => "<button class=dark>" }),
  createCheckbox: () => ({ render: () => "<input class=dark type=checkbox>" }),
};

function renderForm(ui: UIFactory) {
  return [ui.createButton(), ui.createCheckbox()].map((w) => w.render()).join("\n");
}

renderForm(prefersDark ? darkTheme : lightTheme);
```

**TS shortcut:** factories can be plain object literals typed by the interface, as above. Classes are only needed when the factory holds state.

**Pitfalls:** adding a new product kind means touching every factory.

---

## Builder

[refactoring.guru](https://refactoring.guru/design-patterns/builder/typescript/example)

**Intent:** Construct complex objects step by step; the same construction process can produce different representations.

**Use when:** a constructor has many optional parameters ("telescoping constructor"), or construction has ordered steps / validation.

```ts
interface HttpRequest {
  readonly method: "GET" | "POST" | "PUT" | "DELETE";
  readonly url: string;
  readonly headers: Readonly<Record<string, string>>;
  readonly body?: string;
  readonly timeoutMs: number;
}

class RequestBuilder {
  private method: HttpRequest["method"] = "GET";
  private headers: Record<string, string> = {};
  private body?: string;
  private timeoutMs = 30_000;

  constructor(private readonly url: string) {}

  post(body: unknown): this {
    this.method = "POST";
    this.body = JSON.stringify(body);
    return this.header("Content-Type", "application/json");
  }
  header(name: string, value: string): this { this.headers[name] = value; return this; }
  timeout(ms: number): this { this.timeoutMs = ms; return this; }

  build(): HttpRequest {
    if (this.method === "GET" && this.body) throw new Error("GET cannot have a body");
    return Object.freeze({ method: this.method, url: this.url, headers: { ...this.headers }, body: this.body, timeoutMs: this.timeoutMs });
  }
}

const req = new RequestBuilder("/api/users").post({ name: "Ada" }).timeout(5_000).build();
```

A **Director** is optional: a function that runs a fixed sequence of builder steps (e.g. `buildJsonPost(builder, payload)`).

**TS shortcut:** for simple cases, an options object with defaults (`{ timeoutMs = 30_000, ...rest }: Partial<Options>`) replaces a builder. Use a builder when steps need ordering, validation, or produce immutable results.

**Pitfalls:** more code than an options object; returning `this` makes subclassing builders awkward without polymorphic `this` (which TS supports, as shown).

---

## Prototype

[refactoring.guru](https://refactoring.guru/design-patterns/prototype/typescript/example)

**Intent:** Copy existing objects without making code dependent on their classes.

**Use when:** you need copies of objects whose concrete class you don't know, or creating from scratch is expensive and you'd rather clone a preconfigured instance.

```ts
interface Cloneable<T> { clone(): T; }

class Shape implements Cloneable<Shape> {
  constructor(public x: number, public y: number, public color: string, public tags: string[] = []) {}
  clone(): Shape {
    return new Shape(this.x, this.y, this.color, [...this.tags]); // deep-copy mutable fields
  }
}

class Circle extends Shape {
  constructor(x: number, y: number, color: string, public radius: number, tags: string[] = []) {
    super(x, y, color, tags);
  }
  override clone(): Circle {
    return new Circle(this.x, this.y, this.color, this.radius, [...this.tags]);
  }
}

// Prototype registry
const presets = new Map<string, Shape>([["big-red-circle", new Circle(0, 0, "red", 100)]]);
const c = presets.get("big-red-circle")!.clone();
```

**TS shortcut:** for plain data, use `structuredClone(obj)` or spread (`{ ...obj }` is shallow). `structuredClone` loses class prototypes and methods, so implement `clone()` for class instances.

**Pitfalls:** circular references and shared nested mutable state; forgetting to override `clone()` in a subclass silently returns the parent type.

---

## Singleton

[refactoring.guru](https://refactoring.guru/design-patterns/singleton/typescript/example)

**Intent:** Ensure a class has only one instance and provide a global access point to it.

**Use when:** exactly one instance must exist (a shared connection pool, a process-wide registry) and you need stricter control than a global variable.

```ts
class Config {
  private static instance?: Config;
  private constructor(private readonly values: Record<string, string>) {}

  static getInstance(): Config {
    return (Config.instance ??= new Config({ ...process.env } as Record<string, string>));
  }
  get(key: string) { return this.values[key]; }
}

Config.getInstance().get("NODE_ENV");
```

**TS shortcut (preferred):** ES modules are evaluated once, so a module export is already a singleton:

```ts
// config.ts
export const config = loadConfig();
```

Pass it into consumers as a parameter (dependency injection) so tests can supply a different instance.

**Pitfalls:** hides dependencies, couples code to global state, makes tests leak state between runs. Violates single responsibility (manages its own lifecycle). Multiple bundles or duplicated packages in `node_modules` can each get their own "singleton".
