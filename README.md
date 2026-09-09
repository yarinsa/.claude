# .claude

Personal [Claude Code](https://claude.com/claude-code) configuration: portable skills, kept in version control.

## Skills

| Skill | What it does |
|---|---|
| [connect-github-mcp](skills/connect-github-mcp) | Set up, diagnose, or repair GitHub MCP servers for Claude Code and Claude Desktop on macOS. Sources the token from the `gh` CLI keychain, so no PAT is ever written to disk. |

## Install

Skills are directories under `~/.claude/skills/`. Symlink so edits track the repo:

```sh
git clone https://github.com/yarinsa/.claude.git ~/Code/dotclaude
ln -s ~/Code/dotclaude/skills/connect-github-mcp ~/.claude/skills/connect-github-mcp
```

Claude Code picks a skill up on next launch and invokes it when a task matches its `description`.

## Conventions

- No secrets. Tokens come from the macOS keychain via `gh auth token`, resolved at spawn time.
- Scripts are idempotent, back up whatever they edit, and can be re-run safely.
- Every skill ships a read-only `diagnose.sh` that reports state without changing it.
