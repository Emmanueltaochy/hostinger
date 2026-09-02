# Hostinger MCP configuration

Claude Code configuration for the [Hostinger API MCP server](https://github.com/hostinger/api-mcp-server)
(`hostinger-api-mcp` on npm), split into one MCP server per Hostinger product area
so that only the tools you need are loaded into context.

## Layout

| File | Scope | Use it when |
| --- | --- | --- |
| `.mcp.json` | Project | You want these servers available to anyone working in this repo. Reads the token from the `HOSTINGER_API_TOKEN` environment variable. |
| `examples/claude.json.windows.example` | User (`%USERPROFILE%\.claude.json`) | Windows, servers available in every project. |
| `examples/claude.json.unix.example` | User (`~/.claude.json`) | macOS/Linux, servers available in every project. |

The only difference between the two user-scope examples is `npx` vs `npx.cmd` —
on Windows the `.cmd` shim is what is actually executable, so a bare `npx` there
fails to spawn.

## Setup

1. Create an API token in the Hostinger panel: **Account → API → Generate token**.
2. Pick a scope:

   **Project scope (recommended for this repo)** — nothing to copy; `.mcp.json`
   is already here. Export the token before launching Claude Code:

   ```bash
   export HOSTINGER_API_TOKEN='...'      # macOS / Linux
   ```
   ```powershell
   $env:HOSTINGER_API_TOKEN = '...'      # Windows PowerShell
   ```

   **User scope** — merge the `mcpServers` block from the example matching your
   OS into your `.claude.json` (`%USERPROFILE%\.claude.json` on Windows,
   `~/.claude.json` elsewhere) and replace `your-token-here` with the real token.

3. Restart Claude Code and run `/mcp` to confirm the servers connected.

Requires Node.js 20 or newer (`engines` constraint of `hostinger-api-mcp`).

## Token handling

The token grants full control of the account's hosting, domains, DNS, billing and
VPS resources. Keep it out of version control:

- Prefer the project-scope `.mcp.json`, which only references `${HOSTINGER_API_TOKEN}`.
- If you use user scope, the token lives in `.claude.json` outside this repo.
- `.gitignore` covers `.env`, `.env.local` and `*.token`; the example files ship
  with the `your-token-here` placeholder and should stay that way.

## Configured servers

| Server | Binary | Covers |
| --- | --- | --- |
| `hostinger-hosting` | `hostinger-hosting-mcp` | Websites, databases, cron jobs, PHP/Node.js settings, file access |
| `hostinger-domains` | `hostinger-domains-mcp` | Domain purchase, transfers, WHOIS profiles, forwarding, nameservers |
| `hostinger-dns` | `hostinger-dns-mcp` | DNS records, validation, snapshots and restores |
| `hostinger-billing` | `hostinger-billing-mcp` | Catalog, subscriptions, payment methods, auto-renewal |
| `hostinger-reach` | `hostinger-reach-mcp` | Contacts, segments, tags, campaigns, automations, forms |
| `hostinger-vps` | `hostinger-vps-mcp` | Virtual machines, firewalls, snapshots, backups, SSH keys, PTR records |

## Other servers available in the package

Not enabled here — add an entry with the matching binary if you need one:

`hostinger-mail-mcp`, `hostinger-ecommerce-mcp`, `hostinger-wordpress-mcp`,
`hostinger-horizons-mcp`, `hostinger-agency-hosting-mcp`, and
`hostinger-api-mcp` (every tool in a single server).

Loading `hostinger-api-mcp` exposes several hundred tools at once, which is why
this config uses the per-product binaries instead.
