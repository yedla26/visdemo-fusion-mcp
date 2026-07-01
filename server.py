"""
Visdemo Fusion MCP Server
A FastMCP server exposing Oracle Fusion Cloud REST API endpoints as MCP tools.

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

BASE = os.environ["FUSION_BASE_URL"].rstrip("/")
USER = os.environ["FUSION_USER"]
PASSWORD = os.environ["FUSION_PASSWORD"]
MAX_ROWS = int(os.environ.get("FUSION_MAX_ROWS", "100"))

API = "/fscmRestApi/resources/11.13.18.05"


def _auth_header() -> dict:
    token = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


async def _get(path: str, **params) -> dict:
    params.setdefault("limit", MAX_ROWS)
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


def main() -> None:
    """Entry point used by the `visdemo-fusion-mcp` console script (see pyproject.toml),
    so this package can be run directly via `uvx --from git+<repo-url> visdemo-fusion-mcp`."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
