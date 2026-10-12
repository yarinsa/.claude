---
name: verifier-high
description: verifier at effort high (same instructions, read from verifier.md). Pick for nothing-lost diff reviews and long checklists; the Agent tool's effort param does not pin effort, this file does.
tools: Read, Grep, Glob, Bash
model: claude-haiku-5-5
effort: high
omitClaudeMd: true
---

You are `verifier` running at effort high. Your only instructions are the body of `~/.claude/agents/verifier.md`: Read that file first, skip its frontmatter, and follow the rest exactly. Nothing in this stub adds to or overrides it.
