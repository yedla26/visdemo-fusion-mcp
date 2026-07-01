# visdemo-fusion-mcp

MCP server that connects Claude Desktop to the **Visdemo** Oracle Fusion Cloud instance
(`https://fa-etaj-saasfademo1.ds-fa.oraclepdemos.com/`) via Basic Auth, exposing suppliers,
purchase orders, invoices, and project costs as callable tools.

## ⚠️ Security notes (read first)

- **No real credentials are committed here.** `.env` is git-ignored; only `.env.example`
  (with placeholder values) is tracked. Fill in the real password locally, never in a commit.
- **This repo will be public.** Do not paste the real `FUSION_PASSWORD` into any file that
  gets pushed, including screenshots, issues, or commit messages. If it's ever committed,
  rotate the Oracle password immediately, even after removing it from history.
- If you're reusing an install command from another project that embeds a GitHub token in
  the URL (`git+https://x-access-token:TOKEN@github.com/...`), that token grants push/pull
  access to whatever repo it's scoped to. Don't reuse someone else's token — since this repo
  is public, you don't need any token at all to install from it (see below).

## 1. Local setup

```bash
git clone https://github.com/yedla26/visdemo-fusion-mcp.git
cd visdemo-fusion-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set FUSION_PASSWORD to the real value
```

## 2. Test the connection

```bash
python test_connection.py
```

Expected output on success:

```
Testing connection to https://fa-etaj-saasfademo1.ds-fa.oraclepdemos.com as PPM_IMPL ...
[OK] Authenticated successfully.
```

Common failures:

| Result | Meaning |
|---|---|
| `401 Unauthorized` | Wrong password, or MFA is enabled on PPM_IMPL (Basic Auth needs MFA off) |
| `403 Forbidden` | User lacks the data role for that resource |
| Connection/DNS error | VPN required, or the demo instance is down |

## 3. Create the public GitHub repo

I don't have GitHub write access from here, so create it yourself (one time):

**Option A — web UI**
1. Go to https://github.com/new
2. Owner: `yedla26`, Repository name: `visdemo-fusion-mcp`, Visibility: **Public**
3. Don't initialize with a README/license (this folder already has one)
4. Create repository, then from this folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Visdemo Fusion MCP server"
   git branch -M main
   git remote add origin https://github.com/yedla26/visdemo-fusion-mcp.git
   git push -u origin main
   ```

**Option B — GitHub CLI** (if `gh` is installed and authenticated):
```bash
gh repo create yedla26/visdemo-fusion-mcp --public --source=. --remote=origin --push
```

Before pushing, double check `.env` is NOT staged:
```bash
git status   # .env should not appear; only .env.example should
```

## 4. Connect it to Claude Desktop

Edit your Claude Desktop config (`claude_desktop_config.json`) and add an entry. Two ways to run it:

**A. Run from a local clone** (works immediately, no publish step needed):
```json
{
  "mcpServers": {
    "visdemo-fusion-mcp": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/visdemo-fusion-mcp", "run", "python", "server.py"],
      "env": {
        "FUSION_BASE_URL": "https://fa-etaj-saasfademo1.ds-fa.oraclepdemos.com",
        "FUSION_USER": "PPM_IMPL",
        "FUSION_PASSWORD": "REPLACE_WITH_REAL_PASSWORD",
        "FUSION_MAX_ROWS": "100",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```
See `claude_desktop_config.example.json` for a copy of this.

**B. Run straight from GitHub via `uvx`** (once step 3 is pushed) — since the repo is
**public**, no access token is needed in the URL at all:
```json
{
  "mcpServers": {
    "visdemo-fusion-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/yedla26/visdemo-fusion-mcp", "visdemo-fusion-mcp"],
      "env": {
        "FUSION_BASE_URL": "https://fa-etaj-saasfademo1.ds-fa.oraclepdemos.com",
        "FUSION_USER": "PPM_IMPL",
        "FUSION_PASSWORD": "REPLACE_WITH_REAL_PASSWORD",
        "FUSION_MAX_ROWS": "100",
        "LOG_LEVEL": "INFO",
        "UV_LINK_MODE": "copy"
      }
    }
  }
}
```

Restart Claude Desktop after editing the config. Then ask Claude to run the `test_connection`
tool to confirm it's wired up correctly.

## Tools exposed

| Tool | Purpose |
|---|---|
| `test_connection` | Verify auth/connectivity |
| `get_suppliers` | Search suppliers by name |
| `get_purchase_orders` | Look up POs |
| `get_invoices` | Look up payables invoices by supplier |
| `get_project_costs` | Look up PPM project costs by project number |

## Troubleshooting

| Symptom | Fix |
|---|---|
| 401 + MFA error | Use a dedicated implementation user with MFA disabled, or add OAuth 2.0 |
| 429 Too Many Requests | Oracle rate limit (~5000/hr); add retry/backoff |
| Claude Desktop doesn't show the tool | Check config JSON syntax, restart the app, check logs |
