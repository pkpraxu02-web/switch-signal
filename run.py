"""Scheduled pipeline = an MCP *client* of the ticmint-intel server.

  python run.py --source fixtures                     # offline demo (synthetic rows, flagged as such)
  python run.py --source csv --path exports/g2.csv    # licensed G2/Capterra export
  python run.py --source trustpilot,csv --path ...    # several sources, one run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from switchsignal import sheets


def unwrap(res):
    if res.isError:
        raise RuntimeError(res.content[0].text if res.content else "tool error")
    data = res.structuredContent
    if data is None:
        data = json.loads(res.content[0].text)
    return data["result"] if isinstance(data, dict) and set(data) == {"result"} else data


async def pipeline(sources: list[str], path: str, pages: int) -> tuple[dict, dict]:
    params = StdioServerParameters(command=sys.executable, args=["-m", "switchsignal.mcp_server"], env=dict(os.environ))
    stats = {"fetched": 0, "new": 0, "errors": []}
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for src in sources:
                try:
                    out = unwrap(await s.call_tool("ingest_reviews", {"source": src, "path": path, "pages": pages}))
                    stats["fetched"] += out["fetched"]
                    stats["new"] += out["new"]
                    stats["errors"] += [f"{src}: {e}" for e in out["errors"]]
                except Exception as e:  # keep the run alive; surface in the Runs sheet
                    stats["errors"].append(f"{src}: {e}")
            stats["analyzed"] = unwrap(await s.call_tool("analyze_pending", {}))["analyzed"]
            d = unwrap(await s.call_tool("draft_pending", {}))
            stats.update(scored=d["scored"], drafted=d["drafted"], flagged=d["flagged_needs_fix"])
            export = unwrap(await s.call_tool("export_rows", {}))
    return stats, export


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="fixtures", help="comma list of fixtures|csv|trustpilot")
    ap.add_argument("--path", default="")
    ap.add_argument("--pages", type=int, default=2)
    a = ap.parse_args()
    t0 = time.time()
    stats, export = asyncio.run(pipeline(a.source.split(","), a.path, a.pages))
    run = sheets.run_record(sources=a.source, fetched=stats["fetched"], new_reviews=stats["new"],
                            analyzed=stats["analyzed"], leads_scored=stats["scored"], drafts=stats["drafted"],
                            drafts_flagged=stats["flagged"], total_leads_in_sheet=len(export["leads"]),
                            errors="; ".join(stats["errors"])[:500], seconds=round(time.time() - t0, 1))
    where = sheets.sync(export, run)
    print(json.dumps({**run, "output": where}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
