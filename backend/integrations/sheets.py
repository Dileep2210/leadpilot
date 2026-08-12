"""Google Sheets logging with a mock fallback.

Live mode requires:
  GOOGLE_SERVICE_ACCOUNT_JSON  - the service account key, as EITHER:
                                   (a) the raw JSON content of the key file
                                       (paste the whole {...} object — this is
                                       the only option that works on Render,
                                       since there's no key file on disk there), or
                                   (b) a path to a JSON key file on disk
                                       (only useful for local dev)
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

SERVICE_ACCOUNT_RAW = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "Leads!A:F")

MOCK_STORE = Path(__file__).resolve().parent.parent / "data" / "mock_sheet.jsonl"
MOCK_STORE.parent.mkdir(parents=True, exist_ok=True)

_sheets_ready = False
_init_error: str | None = None
_service = None

if SERVICE_ACCOUNT_RAW and SHEET_ID:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        if SERVICE_ACCOUNT_RAW.lstrip().startswith("{"):
            # Raw JSON content pasted directly into the env var (Render, etc.)
            info = json.loads(SERVICE_ACCOUNT_RAW)
            _creds = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
        elif Path(SERVICE_ACCOUNT_RAW).exists():
            # A path to a key file on disk (local dev convenience only)
            _creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_RAW,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
        else:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is neither valid JSON (doesn't start "
                "with '{') nor an existing file path"
            )

        _service = build("sheets", "v4", credentials=_creds)
        _sheets_ready = True
    except Exception as exc:
        _init_error = f"{type(exc).__name__}: {exc}"
        _sheets_ready = False


def sheets_mode() -> str:
    return "live" if _sheets_ready else "mock"


def sheets_detail() -> dict[str, Any]:
    """Diagnostic info for /api/health — safe to expose, no secrets included."""
    return {
        "mode": sheets_mode(),
        "sheet_id_configured": bool(SHEET_ID),
        "credentials_configured": bool(SERVICE_ACCOUNT_RAW),
        "init_error": _init_error,
    }


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
