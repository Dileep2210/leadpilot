"""LangGraph agent: raw lead -> structured record -> Sheet log -> drafted
reply -> Slack notification -> compiled result.

Exposes `run_lead_pipeline(raw_text)` as a generator that yields
(step_name, payload) tuples so the API layer can stream progress via SSE.
"""
from __future__ import annotations
from typing import Any, Generator, TypedDict

from langgraph.graph import StateGraph, END

from agent import llm
from integrations import sheets, slack


class LeadState(TypedDict, total=False):
    raw_text: str
    structured: dict[str, Any]
    sheet: dict[str, Any]
    draft_reply: str
    slack: dict[str, Any]


def _node_extract(state: LeadState) -> LeadState:
    structured = llm.extract_lead(state["raw_text"])
    return {"structured": structured}


def _node_log_sheet(state: LeadState) -> LeadState:
    result = sheets.log_lead(state["structured"], state["raw_text"])
    return {"sheet": result}


def _node_draft_reply(state: LeadState) -> LeadState:
    reply = llm.draft_reply(
        state["raw_text"],
        state["structured"].get("need", ""),
        state["structured"].get("urgency", "warm"),
    )
    return {"draft_reply": reply}


def _node_notify_slack(state: LeadState) -> LeadState:
    result = slack.notify(state["structured"])
    return {"slack": result}


def _build_graph():
    graph = StateGraph(LeadState)
    graph.add_node("extract", _node_extract)
    graph.add_node("log_sheet", _node_log_sheet)
    graph.add_node("draft", _node_draft_reply)
    graph.add_node("notify_slack", _node_notify_slack)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "log_sheet")
    graph.add_edge("log_sheet", "draft")
    graph.add_edge("draft", "notify_slack")
    graph.add_edge("notify_slack", END)
    return graph.compile()


_compiled_graph = _build_graph()

NODE_ORDER = ["extract", "log_sheet", "draft", "notify_slack"]

STEP_LABELS = {
    "extract": "Reading lead & extracting fields",
    "log_sheet": "Logging structured lead to Sheet",
    "draft": "Drafting personalized reply",
    "notify_slack": "Notifying Slack",
}


def run_lead_pipeline(raw_text: str) -> Generator[tuple[str, dict[str, Any]], None, None]:
    initial: LeadState = {"raw_text": raw_text}
    for update in _compiled_graph.stream(initial):
        for node_name, node_output in update.items():
            yield node_name, node_output
