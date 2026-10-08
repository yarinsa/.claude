# Structural Patterns

How to assemble objects and classes into larger structures while keeping them flexible and efficient.
Source: [refactoring.guru/design-patterns/structural-patterns](https://refactoring.guru/design-patterns/structural-patterns)

- [Adapter](#adapter)
- [Bridge](#bridge)
- [Composite](#composite)
- [Decorator](#decorator)
- [Facade](#facade)
- [Flyweight](#flyweight)
- [Proxy](#proxy)

---

## Adapter

[refactoring.guru](https://refactoring.guru/design-patterns/adapter/typescript/example)

**Intent:** Let objects with incompatible interfaces collaborate.

**Use when:** you want to use an existing class (third-party SDK, legacy module) whose interface doesn't match what your code expects.

```ts
// What our app expects
interface Logger {
  log(level: "info" | "error", message: string, meta?: object): void;
}

// Third-party API we can't change
class VendorLogger {
  write(entry: { severity: number; text: string; ctx?: string }) { /* ... */ }
}

class VendorLoggerAdapter implements Logger {
  constructor(private readonly vendor: VendorLogger) {}
  log(level: "info" | "error", message: string, meta?: object) {
    this.vendor.write({
      severity: level === "error" ? 3 : 1,
      text: message,
      ctx: meta && JSON.stringify(meta),
    });
  }
}

const logger: Logger = new VendorLoggerAdapter(new VendorLogger());
```

**TS shortcut:** a function adapter is often enough: `const toLogger = (v: VendorLogger): Logger => ({ log: (l, m, meta) => v.write(...) })`.

**Pitfalls:** adapters accumulate translation logic; keep them thin and push business rules elsewhere.

---

## Bridge

[refactoring.guru](https://refactoring.guru/design-patterns/bridge/typescript/example)

**Intent:** Split a large class or a set of closely related classes into two separate hierarchies, abstraction and implementation, that can vary independently.

**Use when:** a class hierarchy grows in two orthogonal dimensions (e.g. `RedCircle`, `BlueCircle`, `RedSquare`...), or you need to swap implementations at runtime.

```ts
// Implementation side
interface Device {
  isEnabled(): boolean;
  enable(): void;
  disable(): void;
  getVolume(): number;
  setVolume(v: number): void;
}

class Tv implements Device { /* ... */ }
class Radio implements Device { /* ... */ }

// Abstraction side
class RemoteControl {
  constructor(protected readonly device: Device) {}
  togglePower() { this.device.isEnabled() ? this.device.disable() : this.device.enable(); }
  volumeUp() { this.device.setVolume(this.device.getVolume() + 10); }
}

class AdvancedRemote extends RemoteControl {
  mute() { this.device.setVolume(0); }
}

new AdvancedRemote(new Radio()).mute();
```

N remotes × M devices = N + M classes instead of N × M.

**Pitfalls:** overkill for a single, cohesive class; the two hierarchies need a stable interface between them.

---

## Composite

[refactoring.guru](https://refactoring.guru/design-patterns/composite/typescript/example)

**Intent:** Compose objects into tree structures and work with them as if they were individual objects.

**Use when:** your model is a tree (file systems, UI component trees, org charts, order line items with bundles) and clients should treat leaves and branches uniformly.

```ts
interface FileNode {
  name: string;
  size(): number;
}

class File implements FileNode {
  constructor(public name: string, private bytes: number) {}
  size() { return this.bytes; }
}

class Folder implements FileNode {
  private children: FileNode[] = [];
  constructor(public name: string) {}
  add(...nodes: FileNode[]) { this.children.push(...nodes); return this; }
  size(): number { return this.children.reduce((sum, c) => sum + c.size(), 0); }
}

const root = new Folder("root").add(
  new File("a.txt", 120),
  new Folder("src").add(new File("index.ts", 900)),
);
root.size(); // 1020
```

**TS shortcut:** for data-only trees, a recursive type plus a recursive function works: `type Node = { kind: "file"; bytes: number } | { kind: "dir"; children: Node[] }`.

**Pitfalls:** putting `add()` on the shared interface forces leaves to throw; keep child management on the composite only (as above) unless uniformity matters more than type safety.

---

## Decorator

[refactoring.guru](https://refactoring.guru/design-patterns/decorator/typescript/example)

**Intent:** Attach new behaviors to objects by placing them inside wrapper objects that contain the behaviors.

**Use when:** you need to add responsibilities (caching, logging, retry, compression, auth) at runtime and combine them freely, without a subclass for every combination.

```ts
interface DataSource {
  read(key: string): Promise<string | undefined>;
}

class HttpSource implements DataSource {
  async read(key: string) { return (await fetch(`/kv/${key}`)).text(); }
}

class CachingSource implements DataSource {
  private cache = new Map<string, string | undefined>();
  constructor(private readonly inner: DataSource) {}
  async read(key: string) {
    if (!this.cache.has(key)) this.cache.set(key, await this.inner.read(key));
    return this.cache.get(key);
  }
}

class RetryingSource implements DataSource {
  constructor(private readonly inner: DataSource, private readonly attempts = 3) {}
  async read(key: string) {
    for (let i = 1; ; i++) {
      try { return await this.inner.read(key); }
      catch (e) { if (i >= this.attempts) throw e; }
    }
  }
}

const source: DataSource = new CachingSource(new RetryingSource(new HttpSource()));
```

**TS shortcut:** higher-order functions decorate functions directly: `const withRetry = <A extends unknown[], R>(fn: (...a: A) => Promise<R>) => async (...a: A) => { ... }`. TypeScript's `@decorator` syntax is a language feature for annotating classes/methods; it can implement this pattern but is not required for it.

**Pitfalls:** wrapper order matters (cache outside retry vs inside); every decorator must forward the full interface; debugging deep wrapper stacks is harder.

---

## Facade

[refactoring.guru](https://refactoring.guru/design-patterns/facade/typescript/example)

**Intent:** Provide a simplified interface to a library, a framework, or any complex set of classes.

**Use when:** clients need a small slice of a complex subsystem, or you want to layer a subsystem behind a single entry point.

```ts
// Complex subsystem pieces
class VideoDecoder { decode(path: string) { /* ... */ return new Uint8Array(); } }
class AudioMixer { normalize(data: Uint8Array) { return data; } }
class Encoder { encode(data: Uint8Array, format: "mp4" | "webm") { return new Blob([data]); } }

// Facade
export class VideoConverter {
  private decoder = new VideoDecoder();
  private mixer = new AudioMixer();
  private encoder = new Encoder();

  convert(path: string, format: "mp4" | "webm"): Blob {
    const raw = this.decoder.decode(path);
    return this.encoder.encode(this.mixer.normalize(raw), format);
  }
}
```

**TS shortcut:** a module exporting a few functions and not re-exporting the internals is a facade.

**Pitfalls:** a facade can become a god object coupled to everything; split into several facades by use case if it grows.

---

## Flyweight

[refactoring.guru](https://refactoring.guru/design-patterns/flyweight/typescript/example)

**Intent:** Fit more objects into RAM by sharing common parts of state between multiple objects instead of keeping all data in each object.

**Use when:** the app creates a huge number of similar objects and memory is the bottleneck. Split state into **intrinsic** (shared, immutable) and **extrinsic** (unique, passed in by the caller).

```ts
// Intrinsic, shared
class TreeType {
  constructor(readonly name: string, readonly color: string, readonly texture: ImageBitmap) {}
  draw(ctx: CanvasRenderingContext2D, x: number, y: number) { ctx.drawImage(this.texture, x, y); }
}

class TreeTypeFactory {
  private static cache = new Map<string, TreeType>();
  static get(name: string, color: string, texture: ImageBitmap): TreeType {
    const key = `${name}|${color}`;
    let t = this.cache.get(key);
    if (!t) this.cache.set(key, (t = new TreeType(name, color, texture)));
    return t;
  }
}

// Extrinsic, per instance
interface Tree { x: number; y: number; type: TreeType; }

const forest: Tree[] = [];
function plant(x: number, y: number, name: string, color: string, tex: ImageBitmap) {
  forest.push({ x, y, type: TreeTypeFactory.get(name, color, tex) });
}
```

**Pitfalls:** only pays off at real scale; trades RAM for CPU and code complexity. Shared state must be immutable.

---

## Proxy

[refactoring.guru](https://refactoring.guru/design-patterns/proxy/typescript/example)

**Intent:** Provide a substitute for another object that controls access to it, letting you do something before or after the request reaches the original.

**Variants:** virtual (lazy init), protection (access control), remote (network), logging, caching, smart reference.

```ts
interface ReportService {
  generate(id: string): Promise<string>;
}

class RealReportService implements ReportService {
  constructor() { /* expensive: opens DB connections */ }
  async generate(id: string) { return `report ${id}`; }
}

class GuardedLazyReportService implements ReportService {
  private real?: RealReportService;
  constructor(private readonly canAccess: (id: string) => boolean) {}

  async generate(id: string) {
    if (!this.canAccess(id)) throw new Error("Forbidden");      // protection proxy
    this.real ??= new RealReportService();                       // virtual proxy
    return this.real.generate(id);
  }
}
```

**TS shortcut:** the built-in `Proxy` object intercepts arbitrary property access, useful for generic logging or validation proxies, but loses some type safety and readability compared to an explicit class.

**Pitfalls:** extra indirection and latency; response may be delayed by the proxy's work.
