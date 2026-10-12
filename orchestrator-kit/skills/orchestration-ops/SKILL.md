---
name: orchestration-ops
description: Operational how-to for multi-agent work in Claude Code - worktree isolation for concurrent writers, harness task-list mirroring, recovering a silent agent's report from its transcript, the agent-team delivery contract, and the config-efficiency measurement checklist. Load when a wave has 3+ writers, a delegated agent goes idle without a report, or agent usage is being measured.
---

# Orchestration ops

## Concurrent writers
- Before a wave, list the files each leg touches. A file in two legs → serialize those legs or give each writer `isolation: "worktree"`. Two agents writing one file is last-write-wins: silent, no conflict, no error.
- Worktrees for writers only; never for read-only agents (scout, critics, researcher, Explore, Plan, gate).
- Queued rows encode order ("waits on #N"); launch a queued row when its dependency lands, not when the wave finishes.
- Reuse idle agents: a finished agent keeps its context - SendMessage it follow-up work in its lane instead of spawning a cold replacement. Subagent cache TTL is 1h (`subagentPromptCacheTtl`), so a resume inside the hour reads the warm cache.

## Harness task list
- At 3+ workstreams or work spanning turns, mirror the board in TaskCreate/TaskUpdate: one task per row, attributed to the agent's full `<model>-<version>-<effort>-<handle>` name, in_progress on launch, completed only on verified landing.
- Never set a task's `owner` to your own name - the assignment routes back to you as a noise turn.

## Silent agent - idle, no report
1. Read the tail of `~/.claude/projects/<project-slug>/<session-id>/subagents/agent-a<name>-*.jsonl` and recover the last text block.
2. Nothing there → SendMessage it ONCE restating the return contract.
3. Still nothing → ❌ on the board; re-staff, or do it yourself and name the result unreviewed.
Idle-without-report is almost always transport, not the agent. After one stranding, spawn the session's remaining legs with `run_in_background: false`.

## Agent-team teammates (spawned as a team, SendMessage-addressable - not plain subagents)
Their plain final text is not delivered. End every teammate prompt with this, verbatim:
"You run in the background: plain final text is NOT delivered to anyone. When finished or blocked, deliver your complete report by calling SendMessage(to: 'team-lead') - a report not sent through SendMessage does not exist. If you cannot finish everything, send what you have with the rest marked NOT ASSESSED - partial now beats complete never."
Whether teammates auto-notify like subagents is unverified; keep the contract until observed.

## Tier 2 - full gate at the push boundary (lifecycle step 7 / 9)
- Triggers: about to push, open or ready a PR, hand work to a person (another engineer, a PR-finalizing or review-response workflow), or the user asks for proof. A subagent returning to the main loop is NOT a hand-off.
- `gate` runs the project's typecheck, lint, test and build targets on the touched projects (example, TypeScript monorepo: `nx run <project>:{typecheck,lint,test,build}`); done-critic reviews the diff in parallel and reruns Tier 1 only. Both background, one message.
- Exercise the real flow end-to-end (run the app, hit the endpoint, drive the UI, inspect the DB row or emitted event) plus one failure path you touched: error propagation, empty result, boundary, permission/tenant isolation.
- Exactly one full gate per push - never per agent or leg, never in the main loop; the main loop reads the verdict, never raw output. Re-gate only if fixes changed code.

## Measurement - re-run the usage script ~2 weeks after a config change; read directions, not deltas
| Number | Expected |
|---|---|
| Median first-turn cache_creation | down |
| Main-loop tokens per turn | down 10-20% |
| Opus share of subagent runs | toward ~25% |
| Main-loop Bash calls per 45 days | under 1,500 |
| Main-loop tool results over 50 lines | under 100 |
| `general-purpose` share of Agent calls | under 15% |
| Runs with a failed tool call | a rise is the downgrade tripwire |
