---
name: connect-capsule-github
description: Set up, diagnose, or repair GitHub MCP servers for Claude Code and Claude Desktop on macOS, using the gh CLI keychain token instead of a plaintext PAT. Covers the github-projects server (Projects V2, preferred) and the legacy remote github server. Use when a GitHub MCP server fails to connect (401, "badly formatted" Authorization header, "not valid MCP server configurations"), when GitHub Projects v2 data is missing or returns null, or when setting up a new machine.
---

# Connect Capsule GitHub MCP

Wires a GitHub MCP server into Claude Code and Claude Desktop with no token stored in plaintext.

## Which server

**`github-projects` (Arclio `mcp-github-projects`) is the current choice.** GitHub's own remote MCP server has weak Projects V2 coverage, which is the main use case here. Run `scripts/setup-github-projects.sh`.

The legacy remote server (`https://api.githubcopilot.com/mcp/`, via the `github@claude-plugins-official` plugin) is still documented below because its failure modes recur and the setup scripts remain useful. Do not run both: they collide on the server name `github`, and the setup script disables the plugin at local scope.

Third-party server, so two things to weigh: it receives a token with `repo` write scope, and `uvx` resolves the newest PyPI release on every launch. Pin with `PIN=4.0.3 scripts/setup-github-projects.sh` to fix the audit surface.

## Core facts

These were established by testing on macOS. They explain every failure mode below.

1. **Claude Code and Claude Desktop use different config formats.**
   Claude Code (`~/.claude.json`, plugin `.mcp.json`) supports `"type": "http"` remote servers.
   Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`) supports **stdio only**. An `http` entry there is rejected with `not valid MCP server configurations and were skipped`. Remote servers need a stdio proxy (`mcp-remote`) or the Connectors UI.

2. **`$VAR` is not expanded. `${VAR}` is.**
   A header of `Bearer $GITHUB_PERSONAL_ACCESS_TOKEN` is sent literally and the endpoint returns `400 ... Authorization header is badly formatted`.

3. **Fine-grained PATs usually cannot read Projects v2.**
   Missing permission returns a silent `null`, not an error. Detect with the GraphQL probe in `scripts/diagnose.sh`. The `gh` CLI OAuth token (`gho_…`) carries the `project` scope and works for both the MCP endpoint and Projects v2, so prefer it.

4. **A running process never sees a new env var.**
   `/mcp` reconnect re-reads the frozen `process.env`, so it cannot fix a stale token. Only a full app restart works. Claude Code must be relaunched from a **new** terminal.

5. **`~/.claude/settings.json` has an `env` block that overrides the shell.**
   Claude Code injects those values into its own process, so a `GITHUB_PERSONAL_ACCESS_TOKEN` there silently beats anything `~/.zshrc` exports and survives restarts. It is the first place to look when a token fix "does not take". `env` values are static strings and cannot call `gh`, so delete the key rather than trying to make it dynamic. `scripts/scrub-tokens.sh` checks this file.

6. **GUI apps do not source `~/.zshrc`.**
   A Dock-launched app gets a minimal `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`) and none of your exports. Two consequences: use a LaunchAgent to publish env vars to GUI apps, and set `PATH` explicitly inside any stdio `command`, or `npx` dies with `env: node: No such file or directory`.

7. **`gh auth token` reads the keychain fine from a stripped environment.**
   So a stdio server can fetch the token at spawn time and nothing is written to disk.

## Design

Token source is the macOS keychain via `gh`. Nothing plaintext anywhere.

- **Claude Code** reads `GITHUB_PERSONAL_ACCESS_TOKEN` from the environment. `~/.zshrc` sets it to `$(gh auth token)`, evaluated per shell.
- **Claude Desktop** spawns `/bin/sh -c` which runs `gh auth token` at server start. It does not depend on the env var at all.
- The LaunchAgent publishes the token to GUI apps generally, for anything else that wants it.

## Usage

Run in order. Each script is idempotent and backs up what it edits.

```sh
scripts/diagnose.sh                 # read-only; run first and after every change
scripts/setup-github-projects.sh    # PREFERRED server; both clients; removes legacy `github`
scripts/scrub-tokens.sh             # find and redact plaintext tokens on disk
scripts/install-launchagent.sh      # optional; GUI env var, survives reboot

# legacy remote `github` server only:
scripts/setup-claude-code.sh        # zshrc + remove duplicate/stale MCP entries
scripts/setup-claude-desktop.sh     # stdio mcp-remote proxy
```

`setup-github-projects.sh` smoke-tests the server under `env -i` with a minimal PATH before writing any config, so a GUI-only failure surfaces at setup rather than at first use. It reads `PROJECT_DIR` (default `~/Code/capsule`) for the Claude Code project scope.

Then **restart both apps**. Claude Code from a new terminal window.

Verify: `echo ${GITHUB_PERSONAL_ACCESS_TOKEN:0:4}` should print `gho_`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `github-projects` missing after setup | app not restarted | full restart, new terminal |
| Projects tools absent but server connects | `gh` token lacks `project` scope | `gh auth refresh -s project` |
| `400 Authorization header is badly formatted` | `$VAR` instead of `${VAR}` | `setup-claude-code.sh` |
| `401 AUTH_HEADER_REJECTED` after a config fix | stale token in the running process | full restart, new terminal |
| `401` after a genuine restart | stale token pinned in `~/.claude/settings.json` `env` | `scrub-tokens.sh`, delete the key |
| `401` and settings.json is clean | `gh` logged out, or token lacks scope | `gh auth login`, then `diagnose.sh` |
| `not valid MCP server configurations` | `http` entry in the Desktop config | `setup-claude-desktop.sh` |
| Projects v2 returns `null`, no error | token lacks org Projects permission | use the `gh` token, not a PAT |
| `env: node: No such file or directory` | GUI `PATH` lacks Homebrew | already handled in the Desktop entry |
| Desktop works after reboot, then breaks | LaunchAgent runs at login only | `launchctl kickstart gui/$(id -u)/com.claude.ghtoken` |

## Notes

- The LaunchAgent has `RunAtLoad` only. It fires once per login, not on app launch or wake. Add `StartInterval` or `WatchPaths` on `~/.config/gh/hosts.yml` if you rotate tokens often.
- Duplicate `github` server names across user, project, and plugin scope collide. Keep exactly one. The official `github@claude-plugins-official` plugin already ships the correct config, so let it own the name and delete hand-rolled entries.
- If `gh auth logout` ever runs, the servers fail closed rather than falling back to a stale credential. That is intentional.
- Fallback if the keychain is unavailable in some context: hardcode the token in the Desktop config, which is `0600`. Last resort only.
- The Arclio README suggests `env: {"GITHUB_TOKEN": "your_pat_here"}`, which puts a plaintext PAT in the config. The scripts use a `/bin/sh -c` wrapper that calls `gh auth token` at spawn instead.
- `github@claude-plugins-official` may be enabled in a repo's shared `.claude/settings.json`. Disable at **local** scope so the team's file is not modified: `claude plugin disable github@claude-plugins-official --scope local`.
