import type { StepEvent } from "../types";

interface ActiveLabel {
  node: string;
  label: string;
}

interface Props {
  steps: StepEvent[];
  activeLabel: ActiveLabel | null;
  isRunning: boolean;
}

function noteForStep(step: StepEvent): string | null {
  const out = step.output as Record<string, any>;
  if (step.node === "extract" && out.structured) {
    const s = out.structured;
    return `${s.name || "Name not found"} · ${String(s.urgency).toUpperCase()} urgency`;
  }
  if (step.node === "log_sheet" && out.sheet) {
    return out.sheet.mode === "live"
      ? `Row ${out.sheet.row_number ?? "?"} written to your Sheet`
      : "Logged to local demo store (no Sheet connected)";
  }
  if (step.node === "draft" && out.draft_reply) {
    return "Reply drafted — ready to review below";
  }
  if (step.node === "notify_slack" && out.slack) {
    return out.slack.posted ? "Posted to Slack" : "Composed (Slack not connected)";
  }
  return null;
}

export default function StepTrail({ steps, activeLabel, isRunning }: Props) {
  if (steps.length === 0 && !isRunning) {
    return (
      <div className="trail-placeholder">
        Run a lead through the agent to see each step happen live — extraction, Sheet
        logging, reply drafting, and Slack notification.
      </div>
    );
  }

  return (
    <div className="trail-list">
      {steps.map((step) => {
        const note = noteForStep(step);
        return (
          <div key={step.node} className="trail-step done">
            <div className="trail-step-label">
              <span className="check-icon">✓</span>
              {step.label}
            </div>
            {note && <div className="trail-step-note">{note}</div>}
          </div>
        );
      })}
      {activeLabel && (
        <div className="trail-step active">
          <div className="trail-step-label">
            <span className="spinner" />
            {activeLabel.label}
          </div>
        </div>
      )}
    </div>
  );
}
