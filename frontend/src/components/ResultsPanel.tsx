import type { LeadResult } from "../types";

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <div className="lead-field-label">{label}</div>
      <div className={`lead-field-value ${!value ? "empty" : ""}`}>{value || "Not found"}</div>
    </div>
  );
}

export default function ResultsPanel({ result }: { result: LeadResult }) {
  const { structured, sheet, draft_reply, slack } = result;

  return (
    <div className="results">
      <div className="result-card">
        <h3>
          Structured lead
          <span className={`urgency-pill urgency-${structured.urgency}`}>{structured.urgency}</span>
        </h3>
        <div className="lead-grid">
          <Field label="Name" value={structured.name} />
          <Field label="Company" value={structured.company} />
          <Field label="Contact" value={structured.contact} />
          <Field label="Budget signal" value={structured.budget_hint} />
        </div>
        <div style={{ marginTop: 14 }}>
          <div className="lead-field-label">Summarized need</div>
          <div className="lead-field-value">{structured.need || "—"}</div>
        </div>
      </div>

      <div className="result-card">
        <h3>Sheet log</h3>
        {sheet.mode === "live" && sheet.sheet_url ? (
          <a className="sheet-link" href={sheet.sheet_url} target="_blank" rel="noreferrer">
            View row {sheet.row_number} in Google Sheets ↗
          </a>
        ) : (
          <div className="lead-field-value">Row #{sheet.row_number ?? "—"} written to the demo store</div>
        )}
        {sheet.note && <div className="note-line">ⓘ {sheet.note}</div>}
      </div>

      <div className="result-card">
        <h3>Drafted reply</h3>
        <div className="mono-block">{draft_reply}</div>
        <div className="note-line">ⓘ Shown as a draft — not actually sent from this demo.</div>
      </div>

      <div className="result-card">
        <h3>Slack notification</h3>
        <div className="mono-block">{slack.message}</div>
        {slack.note && <div className="note-line">ⓘ {slack.note}</div>}
      </div>
    </div>
  );
}
