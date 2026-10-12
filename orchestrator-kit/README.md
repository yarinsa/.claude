# Claude Code orchestrator kit

A drop-in config that makes the main Claude Code loop act as a team lead. It delegates by default, routes each task shape to a pinned model and effort lane, verifies returned claims cheaply, reports progress on a status board, and keeps its own context clean.

## What it is

- **Main loop** (Fable 5.1) decomposes, staffs agents, verifies, reports. It reads at most one bounded file inline; everything else is delegated.
- **Lanes** are agent files with pinned model and effort: Haiku 5.5 for locating, reconnaissance, verifying, mechanical edits, the gate and bounded small code changes; Sonnet 5.5 for repo coding, plans and research; Opus 5.5 for root-cause investigation and critics. Effort lives in agent frontmatter because the Agent tool's `effort` param is ignored on named spawns.
- **Rules** live in `agent-playbook.md`: lifecycle (steps 1-11), the one size gate, routing table, naming `<model>-<version>-<effort>-<handle>`, string-matched escalation ladder, Haiku lane limits, the delegation prompt, stranded-agent handling, claim verification, status board, Tier 1 / Tier 2 verification, end-of-turn rules.
- **Hooks** inject a safety and return-format preamble into every sub-agent, add a two-line reminder on every user prompt (survives compaction), and send an optional idle desktop notification.
- **Output contract** caps every reply (main and sub-agent) so findings stay short and nothing is dropped.

## Layout

| Path | Install to |
|---|---|
| `CLAUDE.md.snippet` | append to `~/.claude/CLAUDE.md` |
| `agent-playbook.md` | `~/.claude/agent-playbook.md` |
| `rules/*.md` | `~/.claude/rules/` (auto-loads, no import line) |
| `subagent-preamble.md` | `~/.claude/subagent-preamble.md` |
| `agents/*.md` | `~/.claude/agents/` |
| `skills/orchestration-ops/` | `~/.claude/skills/orchestration-ops/` |
| `hooks/*.sh` | `~/.claude/hooks/` (keep executable) |
| `settings.hooks.json` | merge its `hooks` block into `~/.claude/settings.json` |
| `ORCHESTRATOR-PROMPT.md` | alternative to all of the above, paste only |

## Install

```bash
K=./claude-orchestrator-kit; C=~/.claude
mkdir -p $C/agents $C/rules $C/hooks $C/skills
cp $K/agent-playbook.md $K/subagent-preamble.md $C/
cp $K/rules/*.md $C/rules/
cp $K/agents/*.md $C/agents/
cp -r $K/skills/orchestration-ops $C/skills/
cp $K/hooks/*.sh $C/hooks/ && chmod +x $C/hooks/*.sh
cat $K/CLAUDE.md.snippet >> $C/CLAUDE.md     # first line is the playbook import
```

Then merge `settings.hooks.json` into `~/.claude/settings.json`. If you already have a `hooks` key, add each event's entry to your existing arrays instead of replacing them. Restart Claude Code. Check it took: spawn any agent and ask it to quote its first rule (it should be the production-database rule); type a prompt and look for the `[reminder]` lines.

Notes:
- `hooks/subagent-preamble.sh` needs `jq` or `python3`. `hooks/idle-notify.sh` is optional, uses `notify-send` (Linux) and `jq`; on macOS replace the `notify-send` call with `osascript -e 'display notification ...'` or drop the Stop hook.
- Model ids in agent frontmatter are `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`. Edit them if your account exposes different ids.
- Done-critic and simplifier variants (`-high`, `-xhigh`) are thin stubs that read the base file; they exist because only an agent file pins effort.
- `agents/simplifier*.md` need the `simplify` skill; delete them if you lack it.

## Customize

1. **Gate and Tier 1 commands.** `agents/gate.md` uses `<runner>` placeholders; `agents/small-coder.md`, `subagent-preamble.md` and the playbook give a TypeScript example (`tsc`, `eslint`, `vitest`). Replace with your stack's typecheck, lint, covering-test commands. Example (TypeScript monorepo): `nx run <project>:{typecheck,lint,test,build}`.
2. **Project agents.** Add your own coding, test, security and design agents under `<repo>/.claude/agents/`. Name them in the routing table rows "Write or change code" / "Write or fix tests" / "Adversarial security review". They run at the model you pass per call and the effort their own frontmatter sets, else the session's. With none defined, the playbook falls back to `general-purpose` plus a role prompt.
3. **Lane models.** Change `model:` / `effort:` in an agent file, and update the matching playbook table row and naming example so they agree. Keep the escalation ladder consistent with whatever you change.
4. **Safety rules.** The preamble and CLAUDE.md snippet carry two generic rules (no production access without approval, no destroying the local dev database) and a git rule (branch first, draft PRs). Edit or delete them; add your own, one line each.
5. **Optional rules.** `rules/no-third-party-subagent-mcp.md` opts out of other vendors' agent MCP tools; delete it if you use them.
6. **User gate wording** (lifecycle step 10) is a fixed sentence by design; change the text, keep the stop.

## Paste-into-chat quick version

If you cannot install files, open `ORCHESTRATOR-PROMPT.md` and paste everything below its `---` line as the first message, a system prompt, or a project CLAUDE.md. It is self-contained: it lists model and effort per lane, the built-in agent type plus per-call `model:` to use when named agents are absent, and a charter for each lane to paste into the spawn prompt.

Shortest possible version (loses most guards, use only as a stopgap):

```
You are the team lead. Delegate any task needing more than one file read, an unbounded search, a 2+ file change, or reading build/test output. Inline only: one bounded read, one trivial edit, one short command.
Routing (per-call model): locate/search/verify/run/apply-exact-text -> haiku; repo coding, tests, plans, research -> sonnet; root cause, plan review, pre-push diff review -> opus. Reproduce before fixing; every claim cites an observation or is labeled hypothesis.
Every sub-agent returns first line `OK` or `ESCALATE: <reason>`, then <=12 lines of conclusions (a table for 2+ items). On ESCALATE re-issue one lane up: haiku -> sonnet -> opus.
Launch independent legs in one message. Treat returned output as a claim and check it cheaply. One full gate per push, never in the main loop. Post a status board only with 2+ agents in flight. Final message: outcome first, verified vs not, what remains.
```

## Where the pieces come from

Each rule exists to close a failure mode seen in practice: the size gate stops over-planning small fixes; the string-matched escalation stops a cheap lane from arguing its way past its limits; the real-check line stops Haiku reporting done without checking; the stranding rule stops silent agents from stalling a session; the one-gate-per-push rule stops repeated expensive builds.
