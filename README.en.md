# Hostinger MCP configuration

*[Version française](README.md)*

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

The token grants full control of the account's hosting, domains, DNS, billing,
mail and VPS resources. Keep it out of version control:

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
| `hostinger-mail` | `hostinger-mail-mcp` | Mail orders, mailboxes, aliases, forwarders, autoreplies, logs |
| `hostinger-vps` | `hostinger-vps-mcp` | Virtual machines, firewalls, snapshots, backups, SSH keys, PTR records |

## Entry point per panel section

Every Hostinger panel section has one tool that lists its inventory. Start there,
then reuse the identifier it returns (domain name, `username`, order ID, virtual
machine ID) for the detail calls on the same server.

| Panel section | Entry-point tool | MCP server |
| --- | --- | --- |
| Hosting | `hosting_listWebsitesV1` | `hostinger-hosting` |
| Domains | `domains_getDomainListV1` | `hostinger-domains` |
| Billing | `billing_getSubscriptionListV1` | `hostinger-billing` |
| VPS | `VPS_getVirtualMachinesV1` | `hostinger-vps` |
| Mail | `mail_listOrdersV1` | `hostinger-mail` |

These are the tool names as exposed by the MCP server; inside Claude Code they
appear prefixed with the server name, e.g.
`mcp__hostinger-hosting__hosting_listWebsitesV1`.

## Editing WordPress site content

The Hostinger API **does not edit site content**. On WordPress, text and images
live in the database: none of the tools from the servers above can edit a page
or a post. Content goes through the **WordPress REST API**, with access scoped
to a single site.

`scripts/wp.py` wraps that API (Python standard library, nothing to install).

### Creating the access

1. On the site: **Users → Add New**, role **Editor** (not Administrator — an
   Editor changes text and images without being able to touch plugins or delete
   the site).
2. Log in as that user, then **Users → Profile → Application Passwords**. Name
   it, generate it, copy it — it is shown only once. The spaces it contains are
   part of the password.
3. Set the environment variables:

   ```bash
   export WP_SITE_URL='https://mysite.com'
   export WP_USER='my-editor'
   export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'
   ```

An application password is valid for that site only, is revoked on its own from
the same page, and grants nothing beyond the chosen role. It gives no access to
billing, domains, or any other site.

### Commands

| Command | Effect |
| --- | --- |
| `check` | Verify credentials and show the role |
| `detect-builder` | Spot Elementor, Divi, WPBakery… before writing anything |
| `text ID` | List the readable text of a page |
| `find ID "TEXT"` | Locate a text and show the exact raw snippet |
| `replace ID --old A --new B [--apply]` | Replace a text without touching the layout |
| `list [--type pages] [--search TEXT]` | List posts or pages with their IDs |
| `get ID` | Show the raw content |
| `update ID --title T --content-file F` | Change title and/or content |
| `upload IMAGE --alt TEXT` | Send an image to the media library |
| `set-image POST_ID MEDIA_ID` | Set the featured image |

### Page builders: two very different cases

They are not equivalent, and `detect-builder` tells them apart.

**Blocking** — Elementor, Bricks and Beaver Builder keep text in metadata the
REST API does not expose. The `content` field is empty or misleading, and
writing to it destroys the page. `detect-builder` exits with code 2.

**Editable with care** — Divi, WPBakery and Avada/Fusion keep text in the
`content` field, wrapped in their own tags. Editing works through `replace`,
which only touches the targeted text.

On those sites never use `update`: it rewrites the whole content and would take
the layout with it. `replace` saves the original content to
`backup-<type>-<id>.html` before writing, and runs as a simulation by default —
`--apply` is required to actually write.

### Finding the exact text

A builder often splits a sentence with tags: "Notre Expertise" on screen may be
`Notre <span style="…">Expertise</span>` in the markup, so a literal replacement
fails.

`find` bridges the two: it locates on-screen text and prints the real raw
snippet, flagging whether it is contiguous.

```bash
python3 scripts/wp.py find 99641 "Notre Expertise"
```

When the text is split, target a tag-free portion — a single word rather than
the whole sentence — to preserve the formatting.

Sites using the block editor (Gutenberg) or the classic editor need none of
these precautions.

## Other servers available in the package

Not enabled here — add an entry with the matching binary if you need one:

`hostinger-ecommerce-mcp`, `hostinger-wordpress-mcp`, `hostinger-horizons-mcp`,
`hostinger-agency-hosting-mcp`, and `hostinger-api-mcp` (every tool in a single
server).

Loading `hostinger-api-mcp` exposes several hundred tools at once, which is why
this config uses the per-product binaries instead.
