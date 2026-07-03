"""
Visdemo Fusion MCP Server
A FastMCP server exposing Oracle Fusion Cloud REST API endpoints as MCP tools,
plus (optionally) direct JDBC/SQL access to an Oracle database.

Connection details are read from environment variables (see .env.example).
Never hardcode credentials in this file or commit them to git.
"""

from mcp.server.fastmcp import FastMCP
import httpx
import os
import base64
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("visdemo-fusion")

BASE = os.environ["https://epop-dev11.fa.ocs.oraclecloud.com"].rstrip("/")
USER = os.environ["Prabhanand.Yedla@ibm.com"]
PASSWORD = os.environ["Apsdev11@123"]
MAX_ROWS = int(os.environ.get("FUSION_MAX_ROWS", "100"))

API = "/fscmRestApi/resources/11.13.18.05"

# --- Optional direct DB (JDBC-equivalent, via python-oracledb) ---------------
# Only used by run_sql(). Requires DB_HOST/DB_PORT/DB_SERVICE_NAME/DB_USER/DB_PASSWORD
# in .env — these are a SEPARATE Oracle DB connection, not the Fusion REST creds above.
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "1521")
DB_SERVICE_NAME = os.environ.get("DB_SERVICE_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")


def _auth_header() -> dict:
    token = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


async def _get(path: str, **params) -> dict:
    params.setdefault("limit", MAX_ROWS)
    # Fusion's REST API returns 400 Bad Request if q (or other finder params) is
    # present but empty, so drop any blank params instead of sending them as "".
    params = {k: v for k, v in params.items() if v not in ("", None)}
    async with httpx.AsyncClient(timeout=30, verify=True) as client:
        resp = await client.get(f"{BASE}{path}", headers=_auth_header(), params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def test_connection() -> dict:
    """Verify credentials/connectivity against the Visdemo Fusion instance."""
    data = await _get(f"{API}/suppliers", limit=1)
    return {"status": "ok", "sample_count": len(data.get("items", []))}


@mcp.tool()
async def get_suppliers(name_contains: str = "", limit: int = 25) -> dict:
    """Search Oracle Fusion suppliers by name (substring match)."""
    q = f"SupplierName like '%{name_contains}%'" if name_contains else ""
    return await _get(f"{API}/suppliers", q=q, limit=limit)


@mcp.tool()
async def get_purchase_orders(po_number: str = "", limit: int = 25) -> dict:
    """Look up purchase orders, optionally filtered by PO number."""
    q = f"POHeaderId='{po_number}'" if po_number else ""
    return await _get(f"{API}/purchaseOrders", q=q, limit=limit)

@mcp.tool()
async def get_invoices(supplier_name: str = "", limit: int = 25) -> dict:
    """Look up payables invoices, optionally filtered by supplier name."""
    q = f"SupplierName like '%{supplier_name}%'" if supplier_name else ""
    return await _get(f"{API}/invoices", q=q, limit=limit)


@mcp.tool()
async def get_project_costs(project_number: str = "", limit: int = 25) -> dict:
    """Look up project costs (PPM), optionally filtered by project number."""
    q = f"ProjectNumber='{project_number}'" if project_number else ""
    return await _get(f"{API}/projectCosts", q=q, limit=limit)


@mcp.tool()
def run_sql(query: str, max_rows: int = 100) -> dict:
    """
    Run a read-only SQL query directly against the Oracle DB via python-oracledb.

    Requires DB_HOST, DB_SERVICE_NAME, DB_USER, DB_PASSWORD in .env (separate from
    the FUSION_* REST credentials). Only SELECT statements are allowed.
    """
    if not all([DB_HOST, DB_SERVICE_NAME, DB_USER, DB_PASSWORD]):
        return {
            "error": "Missing DB connection env vars. Set DB_HOST, DB_PORT, "
                     "DB_SERVICE_NAME, DB_USER, DB_PASSWORD in .env."
        }

    stripped = query.strip().rstrip(";")
    if not stripped.lower().startswith("select"):
        return {"error": "Only SELECT statements are allowed via run_sql."}

    try:
        import oracledb
    except ImportError:
        return {"error": "python-oracledb is not installed. Run: pip install oracledb"}

    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE_NAME}"
    try:
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(stripped)
                cols = [d[0] for d in cur.description]
                rows = cur.fetchmany(max_rows)
                return {"columns": cols, "rows": [list(r) for r in rows], "row_count": len(rows)}
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    """Entry point used by the `visdemo-fusion-mcp` console script (see pyproject.toml),
    so this package can be run directly via `uvx --from git+<repo-url> visdemo-fusion-mcp`."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
