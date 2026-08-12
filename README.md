# LeadPilot

An AI agent that reads a raw inbound lead (an email, a contact-form message,
a DM) and takes it all the way through: extracts structured fields, logs it
to a Sheet, drafts a personalized reply, and notifies Slack — one pass, no
human steering the middle steps.

Built as a portfolio flagship piece to prove real multi-tool agent
automation (CRM/Sheets + email drafting + Slack), matching the "AI Agent
Automation" service already listed on the portfolio site.

## Stack

- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI (Python)
- **Agent orchestration:** LangGraph
- **LLM:** Gemini (`google-generativeai`)
- **Integrations:** Google Sheets API (service account), Slack Incoming Webhook

## Runs with zero API keys

Every integration has a graceful mock fallback:

| Integration | Live mode needs | Without it |
|---|---|---|
| Extraction + reply drafting | `GEMINI_API_KEY` | Deterministic heuristic extraction (regex-based) |
| Sheet logging | `GOOGLE_SERVICE_ACCOUNT_JSON` + `GOOGLE_SHEET_ID` | Appends to a local `backend/data/mock_sheet.jsonl` |
| Slack notification | `SLACK_WEBHOOK_URL` | Message is composed and shown, not sent |

This means the app is fully runnable and demoable right now, and each
integration switches to "live" independently the moment its credentials are
set — no code changes needed.

## Local development

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in any keys you have, or leave blank for mock mode
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # leave VITE_API_BASE empty to use the dev proxy
npm run dev
```

Visit `http://localhost:5173`. The Vite dev server proxies `/api/*` to
`http://localhost:8000` automatically (see `vite.config.ts`).

## Going live with real integrations

### 1. Gemini (extraction + reply drafting)
Get a key from [Google AI Studio](https://aistudio.google.com/apikey), set
`GEMINI_API_KEY` in `backend/.env`.

### 2. Google Sheets logging
1. Create a Google Cloud project → enable the Sheets API.
2. Create a service account → download its JSON key.
3. Create a Google Sheet, share it with the service account's email
   (found in the JSON key) as an Editor.
4. Set `GOOGLE_SERVICE_ACCOUNT_JSON` to the path of the key file and
   `GOOGLE_SHEET_ID` to the sheet's ID (from its URL).
5. Add a header row to the sheet: `Name | Company | Contact | Need | Urgency | Raw Text`
   on a tab named `Leads` (or update `GOOGLE_SHEET_RANGE`).

### 3. Slack notification
Create an [Incoming Webhook](https://api.slack.com/messaging/webhooks) in a
Slack workspace, set `SLACK_WEBHOOK_URL`.

## Deployment (matches the pattern used for DocsQA / Fieldnote)

- **Backend → Render**: new Web Service, root directory `backend`, build
  command `pip install -r requirements.txt`, start command
  `uvicorn main:app --host 0.0.0.0 --port $PORT`. Add the env vars above in
  Render's dashboard (not in a committed `.env` file).
- **Frontend → Vercel**: root directory `frontend`, framework preset Vite.
  Set `VITE_API_BASE` to your deployed Render URL.

## Project structure

```
leadpilot/
├── backend/
│   ├── main.py                 # FastAPI app, SSE streaming endpoint
│   ├── models.py                # Pydantic schemas
│   ├── agent/
│   │   ├── graph.py             # LangGraph state graph (the agent itself)
│   │   └── llm.py               # Gemini client + mock heuristic fallback
│   └── integrations/
│       ├── sheets.py            # Google Sheets logging + mock fallback
│       └── slack.py             # Slack webhook + mock fallback
└── frontend/
    └── src/
        ├── App.tsx               # Main layout + state
        ├── api.ts                 # SSE stream parsing
        └── components/
            ├── LeadInput.tsx
            ├── StepTrail.tsx
            └── ResultsPanel.tsx
```

## Demo copy for the portfolio card

> **LeadPilot — AI lead intake agent**
> Paste a raw inquiry — the agent extracts the structured details, logs it
> to a Sheet, drafts a personalized reply, and notifies Slack, live and
> visible step by step.
