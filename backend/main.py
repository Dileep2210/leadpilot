from __future__ import annotations
import json
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import time

from agent import llm
from agent.graph import run_lead_pipeline, STEP_LABELS, NODE_ORDER
from integrations import sheets, slack
from models import LeadRequest

app = FastAPI(title="LeadPilot API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins.split(",")] if allowed_origins != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EXAMPLE_LEADS = [
    {
        "label": "Hot — e-commerce, ready to start",
        "text": (
            "Hi, this is Priya Menon from Northwind Retail. We need a full online store built — "
            "product catalog, cart, and Razorpay checkout. We have budget approved ($4k-6k) and "
            "want to launch within 6 weeks, ideally starting this week. My email is priya@northwindretail.in"
        ),
    },
    {
        "label": "Warm — AI feature inquiry",
        "text": (
            "Hey, I'm Marcus, I run a small legal consultancy. We get a lot of repetitive client "
            "questions and I'm wondering if an AI chatbot trained on our internal docs could help. "
            "Not in a rush but would like to explore options. Reach me at marcus@lex-advise.com"
        ),
    },
    {
        "label": "Cold — just browsing",
        "text": (
            "hi saw your portfolio online, just curious what kind of projects you usually do and "
            "roughly what things cost, no specific project in mind right now, just exploring options."
        ),
    },
]


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_mode": llm.llm_mode(),
        "sheets_mode": sheets.sheets_mode(),
        "slack_mode": slack.slack_mode(),
    }


@app.get("/api/examples")
def examples():
    return EXAMPLE_LEADS


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/api/process-lead")
def process_lead(payload: LeadRequest):
    raw_text = payload.raw_text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="raw_text is required")

    def stream():
        final_state: dict = {"raw_text": raw_text}
        try:
            yield _sse("start", {"node": NODE_ORDER[0], "label": STEP_LABELS[NODE_ORDER[0]]})
            time.sleep(0.35)

            idx = 0
            for node_name, node_output in run_lead_pipeline(raw_text):
                final_state.update(node_output)
                yield _sse(
                    "step",
                    {
                        "node": node_name,
                        "label": STEP_LABELS.get(node_name, node_name),
                        "output": node_output,
                    },
                )
                idx += 1
                if idx < len(NODE_ORDER):
                    time.sleep(0.25)
                    yield _sse("start", {"node": NODE_ORDER[idx], "label": STEP_LABELS[NODE_ORDER[idx]]})
                    time.sleep(0.35)

            yield _sse("done", {"result": final_state})
        except Exception as exc:  # pragma: no cover - defensive
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(stream(), media_type="text/event-stream")
