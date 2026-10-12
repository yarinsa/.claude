# Agent Playbook - trigger->action rules; run the matching checklist literally, never from memory

Identical at any parent model/effort; lanes are absolute floors, never pinned to the session.

## Lifecycle - default for bug-fix and feature-dev (‖ = same message, parallel)

| # | Step | Who | Transport |
|---|---|---|---|
| 1 | Classify + size gate | main loop, inline | - |
| 2 | Reconnaissance ‖ branch off the default branch ‖ preflight, warm builds; investigator only when reconnaissance's evidence doesn't name the fix | reconnaissance (haiku) ‖ main loop ‖ mechanic; then investigator | fg |
| 3 | Design -> plan-critic (skipped under the size gate) | Plan -> plan-critic | fg |
| 4 | Implement, backend ‖ frontend, never the same file; each leg runs Tier 1 | domain agent; `small-coder` (haiku) within its bound | fg; bg at 3+ legs |
| 5 | Smoke: the repro + the covering test | implementer | fg |
| 6 | Commit + push the feature branch; CI starts | main loop | - |
| 7 | Full gate ‖ done-critic on the diff | gate ‖ done-critic | bg, one message |
| 8 | Fix findings from 7 and red CI | the idle implementer, via SendMessage | fg |
| 9 | Re-gate only if 8 changed code, then push | gate | fg |
| 10 | USER GATE - post exactly "Branch pushed and gated. Test it locally; say go for the draft PR." and wait (edit the wording to taste, keep the stop) | main loop | - |
| 11 | Open the draft PR on go | main loop, inline | - |

- **SIZE GATE** (the only definition; everything else cites it, never restates the number): confirmed fix surface ≤3 files / ~80 lines, unambiguous, no schema, migration or public-API change -> skip step 3; reconnaissance's `FIX NAMED` or the investigator's FIX SURFACE is the brief; done-critic at 7 is the one review.
- **One gate per push:** a gate covers the push that follows it. Step 6 pushes on a smoke check by design (CI is the first signal, concurrent with 7); step 9's gate covers the second push.
- **Step 2 mechanic:** if the preflight's dependency install fires, it finishes before any test or repro runs - never concurrent with a leg that reads installed dependencies.
- Above the gate, before designing: mirror the codebase's precedent, never a parallel mechanism · name the existing safeguard for the failure you handle, else search before adding one · verify assumptions (repo -> scout, external -> researcher) · resolve plan-critic BLOCKERS · check in with the user before non-trivial implementation.
- Every bug -> reconnaissance FIRST (repro, decisive log lines, call chain, last commits on the touched files); its `FIX NAMED` is a one-edit fix -> `small-coder` with the repro; otherwise -> investigator with reconnaissance's return as the brief, evidence chain required. Every claimed cause or fix carries its observation (log line, code read, command output) or is labeled "hypothesis, unverified". Reproduce before fixing, rerun after; no repro on both sides = a guess.
- Discovery contradicts the plan -> STOP, re-plan, update the task list, tell the user if direction changed. State-changing command (restart/delete/migrate/deploy) -> confirm the evidence supports that specific action; target contradicts its description -> surface it.

## Routing table - task shape -> agent

Named agents carry model/effort in frontmatter; built-ins and your repo's own project agents get a per-call `model:` and run at the effort their own frontmatter sets, else the session's. The Agent tool's `effort` param is ignored on a named spawn (observed: a named scout at `effort: low` ran at the lead's xhigh; an unnamed Explore at `effort: low` ran at low). Under the naming convention every spawn is named, so only frontmatter pins effort. Repo agents (`<repo>/.claude/agents`) are taken as they are: their own `effort:` when set, else the session's - never pinned, copied or edited from here; the name carries the effort in force. Built-ins (Explore, Plan, the catch-all) also run at the session's effort - a local pinned lane (reconnaissance, scout, verifier) comes first. Aliases (pick per row below - the task shape chooses the model, never a blanket default): `haiku` = Haiku 5.5 (`claude-haiku-5-5`: locate, apply, run, verify, digest, inventory, bounded sweeps; $0.10/$0.50 per MTok while the request stays ≤100K tokens, 5x that above and still 4x under Sonnet; the fastest model; effort medium, high for instruction-heavy checks, never xhigh/max - see the Haiku lane) · `sonnet` = Sonnet 5.5 (multi-step repo coding, tests, plans, research, where the routing table names it; $2/$10; effort medium, high for multi-file or vendor facts) · `opus` = Opus 5.5 (judgment: investigator, critics, review, hardest long-horizon; $4/$20; medium, high on escalation) · `fable` = Fable 5.1 (main loop only; $10/$50, last escalation rung). `general-purpose` or Explore when a named lane exists and is installed = routing failure. If the named agent file is not installed, use a built-in (Explore, or general-purpose with the lane's charter in the prompt) with the per-call `model:` the row names; effort then inherits the session's, so a Haiku lane run this way is a degraded fallback: keep the brief to one screen and install the agent file when you can.

| Task shape | Agent | Model-effort | Transport |
|---|---|---|---|
| Find a file, symbol, call site, config value | scout | haiku-5-5-medium | fg |
| Reconnaissance: evidence for a bug (repro, decisive log lines, call chain, last commits on the files), data sweep, inventory, read-only CLI/API digest | reconnaissance; `ESCALATE:` -> investigator (a bug) or Explore `model: sonnet` (a sweep) | haiku-5-5-medium | fg; same message as the leg it feeds |
| Sweep many files for a pattern | scout in sweep mode (table ≤6 rows + total count), one bounded slice per agent; reconnaissance when the sweep needs Bash; Explore `model: sonnet` only when neither slices it | haiku-5-5-medium (frontmatter); Explore inherits the session's effort | fg |
| Verify a landed claim the next step builds on; digest one log / test output / transcript tail; nothing-lost diff review | verifier; `verifier-high` for nothing-lost | haiku-5-5-medium; haiku-5-5-high (own agent file) | gates a push, PR, hand-off or destructive command -> fg, before that step, never in its message; else bg, same message as the dependent step, one verifier per wave |
| Why is this broken, once reconnaissance's evidence doesn't name the fix | investigator, briefed with reconnaissance's return | opus-5-5-medium | fg |
| Third-party API/SDK/vendor fact | researcher | sonnet-5-5-high; `model: haiku` for one fact from one known page (runs at the frontmatter's high) | fg |
| Design a non-trivial change | Plan | `model: sonnet` | fg |
| Review a plan | plan-critic | opus-5-5-medium | fg |
| Small code change: ≤2 files, ≤~40 lines, the brief names what, where (file:line) and the covering test or command | small-coder; `ESCALATE:` -> the project agent at `model: sonnet` | haiku-5-5-high | fg |
| Write or change code | your repo's project agents (backend, frontend, domain owners, designers, writers); none defined -> general-purpose with a role prompt | `model: sonnet` (Sonnet 5.5) at the repo frontmatter's effort, else the session's; `opus` on escalation | fg; bg at 3+ legs |
| Write or fix tests | your repo's test agent; none -> general-purpose with a test-writer role prompt | `model: sonnet` | fg |
| Adversarial security review | your repo's security reviewer; none -> general-purpose with a red-team role prompt | `model: opus` | fg |
| Visual or style-parity sweep (repo-specific auditors, e.g. a dark-mode or token-parity checker) | your repo's auditor agents | `model: haiku` (effort inherits the session's; the repo frontmatter is the only pin) | fg |
| Apply exact text you hold; run a known command; preflight, warm builds, liveness checks | mechanic | haiku-5-5-medium | fg |
| Run the full gate | gate | haiku-5-5-medium | bg |
| Review a finished diff pre-push | done-critic (`-high`, `-xhigh` for logic-heavy, security, migrations, concurrency, very large diffs) | opus-5-5-medium (high / xhigh) | bg |
| Simplify a diff (reuse/quality/efficiency edits, optional) | simplifier (`-xhigh` for the high-risk lane; `model: sonnet` for cosmetic diffs) | opus-5-5-high (xhigh) | fg |

**Naming** (Agent `name`): `<model>-<version>-<effort>-<handle>`, dots -> hyphens: `opus-5-5-medium-investigator`, `sonnet-5-5-medium-be-core`, `haiku-5-5-medium-verifier-wave2`, `fable-5-1-xhigh-core`. The effort segment is the effort in force: the agent's frontmatter `effort:`, else the session's - never the Agent tool's `effort` param, which named spawns ignore.

**Escalation is string-matched, never judged.** Every return starts `OK` or `ESCALATE: <reason>`. `ESCALATE:`, Tier 1 failing twice on one change, or a fix surface over the SIZE GATE -> re-issue the same prompt one lane up: haiku-5-5-(any effort) -> sonnet-5-5-medium -> sonnet-5-5-high -> opus-5-5-medium -> opus-5-5-high -> fable-5-1-high (only on an explicit ESCALATE from opus-5-5-high). A Haiku rung never escalates to a higher Haiku effort - straight to sonnet-5-5-medium (small-coder -> the project agent at `model: sonnet`, except `ESCALATE: preflight needed` -> mechanic preflight, then the same brief back to small-coder; reconnaissance has no sonnet evidence lane: a bug -> investigator, a sweep -> Explore `model: sonnet`). Critics never below opus-5-5-medium; gate reports FAIL, never escalates.

## Haiku lane - bounded, checkable work, beside the leg that thinks (`claude-haiku-5-5`)

Near-free and the fastest model: use it for anything bounded and checkable, launched in the same message as the leg that does the thinking. Never for judgment or design. Code only through `small-coder`, inside its bound, Tier 1 mandatory (the owner's call: offload small coding and reconnaissance to Haiku; its Terminal-Bench score is 39% at max effort vs Sonnet 5.5 at 71%, and it has a documented "reports done without checking" mode - that is why the bound, the real-check line and the straight escalation to sonnet-5-5-medium exist; exact text you already hold is still the mechanic's).

| Effort | Use for | Why |
|---|---|---|
| medium (default) | locate, reconnaissance, bounded sweep, verify, digest, run + report, apply exact text | documented starting point; halves low's early stopping |
| high | nothing-lost diff review, long checklists, `small-coder` code changes | better instruction fidelity, same price class; reached only through a pinned agent file (`verifier-high`, `small-coder`), never the tool param |
| low | not used - no lane pins it; medium is the floor | fastest, but skips searches and checks on anything longer than one step |
| xhigh / max | never on a local lane | ~3x tokens for a few points; the task belongs on sonnet-5-5-medium. A repo agent at `model: haiku` inheriting the session's xhigh is taken as-is |

- **Pin effort in frontmatter.** A Haiku lane is always a named agent under `~/.claude/agents` with `effort:` set (scout, reconnaissance, verifier, mechanic, gate, small-coder); a lane at another effort is its own agent file (`verifier-high`, mirroring `done-critic-high`). A per-call `model: haiku` on a repo agent inherits the session's effort and is taken as-is (visual sweep); on a built-in it is a routing failure - the local pinned lane (reconnaissance, scout, verifier) exists for that work.
- **Budget - the cheap tier is per request.** `omitClaudeMd: true` lanes start at ~12K tokens; a repo agent that loads the CLAUDE.md chain starts at ~40-55K; reading under a directory that holds a CLAUDE.md pulls it in mid-run (a scout went 13K -> 60K in three turns). Bound every scope: name the files or the one output. A scope you can't bound to ≤100K tokens (≈300 KB of text) -> split into parallel scouts, one slice each. Never hand Haiku a whole repo, a whole transcript, or unbounded build-tool output - write it to a file and `tail`/`grep` it.
- **Batch, don't fan.** Every completion wakes the main loop (a turn on cached context on the most expensive model), which costs more than the Haiku run: one verifier per wave carrying all that wave's claims; one scout per slice only when the slices are large.
- **Guard its documented failure modes:** at low/medium it may report a change done without a real check (the prompt template's real-check line is mandatory; Tier 1 runs); it stops early on long briefs (one screen); it skips a search when unsure (say "search before answering not-found").

## Delegation prompt - the whole prompt

```
Goal: <one sentence outcome>
Repo/branch: <abs path> @ <branch>
Files: <abs paths, or "locate them yourself">
Decided already: <constraints not to re-litigate>
Out of scope: <what not to touch>
Return: first line exactly `OK` or `ESCALATE: <reason>`, then <X as file:line + one-line why>, ≤12 lines, 2+ items as a table. Output contract (`rules/output-contract.md`) applies to the return.
Tier 1 only (Verification below); say what you ran. Escalate instead of guessing: over the size gate, a boundary crossed, the named scope too small, or 2 failed Tier-1 runs.
Never background Tier 1/builds/long commands - run foreground and wait; never go idle with uncommitted work or an unsent report.
Before reporting a code change done, run a real check that exercises it (the covering test, typecheck, or the changed command). A syntax-only check or a check that failed to start does not count; if no real check can run, say which one you skipped and why.
```
Safety rules (production/local data stores), the output cap, batch-reads, lane read-only-ness and the no-third-party-sub-agent line reach every subagent via the SubagentStart preamble (`subagent-preamble.md`) - never retype them. Haiku brief: one screen, files named, the check named, "search before answering not-found".

**Transport:** `run_in_background: false` for any result the next step needs; background for parallel fans. Background subagents report automatically on completion. An idle/completion notification naming unfinished work ("waiting on", "running", "will", etc.) is STRANDED, not an echo - same turn: read its transcript tail + `git status` its workspace (skill `orchestration-ops`), then SendMessage it to finish in the foreground now with the exact remaining steps. Idle with nothing left to do -> ❌ on the board and re-staff. Agent-team teammates are not subagents - their prompt still ends with the SendMessage(to: 'team-lead') delivery contract [auto-notification unverified]. CIRCUIT BREAKER: after one stranding spawn the rest foreground; two agents in a row producing nothing usable -> work inline, say so once, name what went unreviewed.

## On every task arrival - route before touching anything

1. Classify: inline case per CLAUDE.md -> inline, no board. Else orchestrate.
2. Decompose into legs with clean file boundaries; a file in two legs -> serialize or `isolation: "worktree"` (skill `orchestration-ops`). Width is bounded by distinct projects touched, not by how many legs you can name - cheap sequential-safe legs go to one agent, not three.
3. Staff by the routing table; name per convention. At 3+ workstreams mirror the board in the harness task list, never with yourself as owner.
4. Launch all independent legs in ONE message, then post the board; a single quick lookup gets a one-line note.
5. While they run: branch, preflight, warm lib builds, scaffolds; verify landed claims (one haiku verifier per wave, launched with the next wave); prep the next wave. Never take an in-flight agent's scope inline or redo a delegated search; reuse an idle agent via SendMessage before spawning a cold one. Larger efforts -> separate delegations per phase, reading each result before deciding the next; never hold the whole effort in the main context.

**Returned output is a claim.** Cheapest rung that settles it: code content -> open the cited line inline · a one-liner settles it -> rerun shaped to emit only the answer (`| wc -l`, `; echo $?`, `diff -q`) · anything else (a build/test/log verdict, several claims at once, a nothing-lost diff, a transcript tail) -> verifier (haiku-5-5-medium), one per wave carrying all that wave's claims - gates a push, PR, hand-off or destructive command -> fg, before that step, never in its message; otherwise bg, launched in the SAME message as the step that builds on them; never rerun in the main loop · nothing cheap and no verifier can reach it -> report it as the agent's unverified claim. REFUTED -> SendMessage the author to correct and the dependent agent to hold; a second REFUTED on the same claim -> investigator, never another author round; never fix inline silently. A verifier verdict never replaces done-critic at a hand-off: config, docs and skills get done-critic on the diff before the hand-off, the same as code - the verifier's nothing-lost verdict is its input, not the review.

## Status board - the one way progress is reported

Subagents in flight -> progress reporting IS the board; sole exception, a single
quick-lookup agent gets a one-line note. Keep it boring, predictable, self-contained.

| # | Agent | Task | Status |
|---|---|---|---|
| 1 | opus-5-5-high-f4-be-core (backend agent) | Provider + column dedup fix | 🔧 running |
| 2 | opus-5-5-medium-f4-qa (done-critic) | E2E proof of the full flow | ⏸ queued - waits on #1 |

- **Statuses - exactly these six, nothing else:** 🔧 running - active <Ns/min ago> · ⏸ queued - waits on
  <#/what> · ⛔ blocked - on <what> · 🔎 review · ✅ done · ❌ failed - <one-line why>.
  Plain-text labels are fine where emoji don't render. No activity on a running row for 5 min -> flip it to ⛔ blocked and act, don't wait for the user to ask.
- **Task** = the outcome in ≤8 plain words traceable to the user's request.
- **CADENCE** - repost the FULL board, never a diff or a partial, at exactly two moments:
  launching a multi-agent wave · a row MATERIALLY changing status (several in one turn ->
  ONE repost after they land). End-of-turn: board only if a row changed. Notification-only
  turns - idle pings, task echoes, background completions that decide nothing - get zero
  or one line, never a board. Fewer than 2 agents in flight -> one-line notes, no board.
  Verifiers and the step-2 mechanic get a one-line note, never a row, and don't count toward
  the 2-in-flight threshold; a REFUTED verdict is a material change and goes in the next board post.
- **Below the board:** ≤3 bullets, only what a table can't carry: a decision the user must make, a discovery that changes the plan, a coordination constraint (shared files, branch discipline, hand-offs).
- **End every board post** with one line: what's running, what's next, who acts next
  (you / an agent / the user).
- **Status question from the user** -> a real liveness check (transcript mtime, process state, `git status`) before answering; never answer from the last report.

## Verification - two tiers; the gate runs once, never in the main loop

**Tier 1** (the only definition) - the implementer, every local iteration: typecheck the config covering your changed files · lint the changed files · run the covering test · bug fix: the repro before and after. Never a build, a whole project's suite, e2e, or a run-everything / run-affected workspace command, or `<test runner> related`/affected-style test selection; prefer the direct binary to the workspace-runner target. Skip a check when nothing it reads changed. Example (TypeScript monorepo): `tsc --noEmit -p <the tsconfig covering your changed files>` (a changed spec file needs the spec tsconfig) · `eslint <changed files> --cache` · `vitest run <the covering spec>`. Preflight when tests are coming or a binary fails module resolution: confirm the workspace is installed (example: `<runner> show projects >/dev/null 2>&1 || CI=true <pkg-manager> install --frozen-lockfile`), then build only the libs the covering test imports - at step 2 a mechanic (haiku) runs the preflight and warm builds so their output never lands in the main loop; an implementer that hits a module-resolution failure mid-iteration reruns the preflight itself (small-coder excepted: it returns `ESCALATE: preflight needed` instead).

**Tier 2 - push boundary:** gate agent (haiku-5-5-medium) ‖ done-critic, exactly one full gate per push, never in the main loop (read the verdict, never raw output). Triggers, commands and the end-to-end proof: `agents/gate.md` + skill `orchestration-ops`.

Name the tier in every report: "Tier 1: typecheck + lint + the 2 covering tests; full gate NOT run" or "full gate green". Never "should work"; never done from a clean compile.

## When ending your turn

Verified, or the unverified named? Final message stands alone under the output contract: outcome first, what changed, verified vs not, what remains. Agents ran this turn -> the end-state board is in the final message and the harness task list matches it. Agents in flight when the turn ends -> a liveness watch is armed (Monitor, a bounded Bash loop on transcript mtime/workspace state, or ScheduleWakeup) that catches a stall within ~5 min, or the turn does not end. Parking multi-session work -> resume memory: branch, commits, done, outstanding, gotchas. Unrelated new task -> suggest a fresh session or /compact. After compaction trust the summary's settled decisions.
