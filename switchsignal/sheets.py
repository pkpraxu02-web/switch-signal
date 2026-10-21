"""Google Sheets sync (service account, free). The Sheet is the human CRM surface:
machine columns are overwritten on every run; human columns (status/owner/notes) are never touched.
Falls back to CSV files when no credentials are configured, so the pipeline never silently drops output."""
from __future__ import annotations

import csv
import json
import os
import pathlib
from datetime import datetime, timezone


def _col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def write_csv(export: dict, run: dict, out_dir: str = "output") -> list[str]:
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, header, rows in (("leads.csv", export["leads_header"] + export["human_header"],
                                [r + ["new", "", ""] for r in export["leads"]]),
                               ("trends.csv", export["trends_header"], export["trends"])):
        with open(p / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        paths.append(str(p / name))
    with open(p / "runs.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(list(run.values()))
    return paths


def sync(export: dict, run: dict) -> str:
    sheet_id, creds = os.getenv("SHEET_ID"), os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not (sheet_id and creds):
        return "csv: " + ", ".join(write_csv(export, run))
    import gspread

    gc = gspread.service_account_from_dict(json.loads(creds))
    sh = gc.open_by_key(sheet_id)

    def ws(title: str, header: list[str]):
        try:
            w = sh.worksheet(title)
        except gspread.WorksheetNotFound:
            w = sh.add_worksheet(title, rows=1000, cols=len(header) + 2)
        if w.row_values(1) != header:
            w.update(range_name="A1", values=[header])
            w.freeze(rows=1)
        return w

    mh, hh = export["leads_header"], export["human_header"]
    leads = ws("Leads", mh + hh)
    existing = leads.col_values(1)  # lead ids in column A, row 1 is the header
    index = {lid: i + 1 for i, lid in enumerate(existing) if i > 0}
    updates, appends = [], []
    last = _col(len(mh))
    for row in export["leads"]:
        if row[0] in index:
            r = index[row[0]]
            updates.append({"range": f"A{r}:{last}{r}", "values": [row]})  # machine cols only
        else:
            appends.append(row + ["new", "", ""])
    if updates:
        leads.batch_update(updates, value_input_option="RAW")
    if appends:
        leads.append_rows(appends, value_input_option="RAW")

    trends = ws("Trends", export["trends_header"])
    trends.clear()
    trends.update(range_name="A1", values=[export["trends_header"]] + export["trends"])

    runs = ws("Runs", list(run.keys()))
    runs.append_row(list(run.values()), value_input_option="RAW")  # one row per run = proof of self-refresh
    return f"sheet {sheet_id}: {len(updates)} updated, {len(appends)} appended"


def run_record(**kw) -> dict:
    return {"run_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), **kw}
