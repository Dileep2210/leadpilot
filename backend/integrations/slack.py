"""Slack notification with a mock fallback.

Live mode requires SLACK_WEBHOOK_URL. Without it, the composed message is
returned but not sent, so the app stays fully demoable.
"""
from __future__ import annotations
import os
from typing import Any

import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()


def slack_mode() -> str:
    return "live" if SLACK_WEBHOOK_URL else "mock"


def notify(structured: dict[str, Any]) -> dict[str, Any]:
    urgency = (structured.get("urgency") or "unknown").upper()
    name = structured.get("name") or "Unknown"
    company = structured.get("company") or "—"
    need = structured.get("need") or "No summary extracted"
    message = f":inbox_tray: *New lead* [{urgency}] — {name} ({company})\n>{need}"

    if SLACK_WEBHOOK_URL:
        try:
            resp = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=8)
            if resp.status_code == 200:
                return {"mode": "live", "posted": True, "message": message, "note": None}
            return {
                "mode": "live",
                "posted": False,
                "message": message,
                "note": f"Slack responded with status {resp.status_code}",
            }
        except Exception as exc:
            return {"mode": "live", "posted": False, "message": message, "note": f"Slack call failed: {exc}"}

    return {
        "mode": "mock",
        "posted": False,
        "message": message,
        "note": "No Slack webhook configured — message composed but not sent.",
    }
