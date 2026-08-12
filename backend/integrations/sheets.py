"""Google Sheets logging with a mock fallback.

Live mode requires:
  GOOGLE_SERVICE_ACCOUNT_JSON  - path to a service account JSON key file
  GOOGLE_SHEET_ID              - the target spreadsheet ID

Without those set, leads are appended to a local JSONL file instead so the
app is fully runnable and demoable without any Google setup.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import Any

SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "Leads!A:F")

MOCK_STORE = Path(__file__).resolve().parent.parent / "data" / "mock_sheet.jsonl"
MOCK_STORE.parent.mkdir(parents=True, exist_ok=True)

_sheets_ready = False
if SERVICE_ACCOUNT_PATH and SHEET_ID and Path(SERVICE_ACCOUNT_PATH).exists():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        _creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_PATH,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        _service = build("sheets", "v4", credentials=_creds)
        _sheets_ready = True
    except Exception:
        _sheets_ready = False


def sheets_mode() -> str:
    return "live" if _sheets_ready else "mock"


def log_lead(structured: dict[str, Any], raw_text: str) -> dict[str, Any]:
    row = [
        structured.get("name") or "",
        structured.get("company") or "",
        structured.get("contact") or "",
        structured.get("need") or "",
        structured.get("urgency") or "",
        raw_text[:500],
    ]

    if _sheets_ready:
        try:
            result = _service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range=SHEET_RANGE,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]},
            ).execute()
            updated_range = result.get("updates", {}).get("updatedRange", "")
            row_number = None
            if "!" in updated_range and ":" in updated_range:
                try:
                    row_number = int("".join(ch for ch in updated_range.split("!")[1].split(":")[0] if ch.isdigit()))
                except ValueError:
                    row_number = None
            return {
                "mode": "live",
                "row_number": row_number,
                "sheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}",
                "note": None,
            }
        except Exception as exc:
            return {
                "mode": "mock",
                "row_number": None,
                "sheet_url": None,
                "note": f"Sheets API call failed, fell back to local log: {exc}",
            }

    # Mock mode
    entry = {"ts": time.time(), "row": row}
    with MOCK_STORE.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    line_count = sum(1 for _ in MOCK_STORE.open()) if MOCK_STORE.exists() else 1
    return {
        "mode": "mock",
        "row_number": line_count,
        "sheet_url": None,
        "note": "No Google Sheets credentials configured — logged to a local demo store instead.",
    }
