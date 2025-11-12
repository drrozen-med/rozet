<!--
2025-11-08T10:38:14+02:00
Purpose: Step-by-step reference for configuring Cursor 2.0 MCP servers used in Rozet.
Related Files: .cursor/mcp.json
-->

# Cursor MCP Server Setup

This guide captures the canonical procedure for registering external Model Context Protocol (MCP) servers with Cursor 2.0. Follow it whenever we need to add, update, or troubleshoot MCP integrations for the Rozet workspace.

## 1. Prerequisites

- Ensure Node.js ≥ 18 is installed and discoverable via `which npx`.
- Verify Cursor 2.0 is installed. These instructions target `~/.cursor/mcp.json`.
- Python tooling for this repo is managed with `uv`; run `uv sync --extra dev` before executing any helper scripts.
- Gather any required service credentials (PostgreSQL connection string, Firebase service account file, etc.).

## 2. Configuration Workflow

1. Locate the configuration file:
   - Global scope: `~/.cursor/mcp.json` (used by all projects).
   - Project scope: `<project>/.cursor/mcp.json` (overrides global when present).
2. Back up the file before large edits.
3. Add or update MCP entries under the top-level `mcpServers` object.
4. Use absolute paths for the `command` field (e.g., output of `which npx`).
5. Prefer environment variables for secrets (e.g., `DATABASE_URL`), keeping credentials out of the repo.
6. Restart Cursor after saving to load the new servers.

## 3. Standard Rozet Entries

We currently rely on the following server packages from the npm `@modelcontextprotocol` namespace:

| Server | Package | Typical Args | Environment Notes | Primary Use |
|--------|---------|--------------|-------------------|-------------|
| Google Chrome DevTools | `@modelcontextprotocol/server-chrome-devtools` | `http://localhost:9222` (the remote debugging URL) | Ensure Chrome is launched with `--remote-debugging-port=9222`. | Inspect DOM, console, and network during UI debugging. |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | _(none)_ | Provide `DATABASE_URL` (e.g., `postgresql://localhost:5432/postgres`). | Run SQL queries and inspect schemas. |
| CHADCN | `@modelcontextprotocol/server-chadcn` | _(none)_ | None. | Browse shadcn/ui component catalog from inside Cursor. |
| Firebase | `@modelcontextprotocol/server-firebase` | _(none)_ | Supply Firebase service account variables as needed. | Query and modify Firebase resources. |

Refer to `.cursor/mcp.json` for the live configuration, including descriptions and environment overrides.

## 4. Validation Checklist

- `npx --version` succeeds from the same shell Cursor will spawn.
- Each MCP entry appears under **Settings → Tools & Integrations → MCP Tools** after restarting Cursor.
- Service-specific health checks:
  - Chrome DevTools: `curl http://localhost:9222/json/version` returns metadata.
  - PostgreSQL: `psql` can connect with the same `DATABASE_URL`.
  - Firebase: Service account file path resolves, and credentials have required permissions.

## 5. References

- Cursor MCP documentation: <https://docs.cursor.com/context/model-context-protocol>
- Model Context Protocol server catalog: <https://github.com/modelcontextprotocol>
- Chrome DevTools remote debugging guide: <https://developer.chrome.com/docs/devtools/open>

Update this guide whenever we add new servers, change package CLI expectations, or rotate credentials.

