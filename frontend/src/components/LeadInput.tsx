import type { ExampleLead } from "../types";

interface Props {
  value: string;
  onChange: (v: string) => void;
  examples: ExampleLead[];
  onPickExample: (text: string) => void;
  onSubmit: () => void;
  isRunning: boolean;
}

export default function LeadInput({ value, onChange, examples, onPickExample, onSubmit, isRunning }: Props) {
  return (
    <div className="panel input-card">
      <label htmlFor="lead-text">Paste a raw lead — an email, a contact-form message, a DM</label>
      <textarea
        id="lead-text"
        value={value}
        maxLength={2000}
        placeholder="e.g. Hi, I'm Sam from Loop Studio, we need a booking system built for our yoga classes, hoping to launch in a month..."
        onChange={(e) => onChange(e.target.value)}
      />

      {examples.length > 0 && (
        <div className="examples-row">
          {examples.map((ex) => (
            <button key={ex.label} className="example-chip" onClick={() => onPickExample(ex.text)} type="button">
              {ex.label}
            </button>
          ))}
        </div>
      )}

      <div className="actions-row">
        <button className="btn-primary" onClick={onSubmit} disabled={isRunning || value.trim().length < 5}>
          {isRunning ? (
            <>
              <span className="spinner" /> Processing…
            </>
          ) : (
            <>Run LeadPilot →</>
          )}
        </button>
        <span className="char-count">{value.length}/2000</span>
      </div>
    </div>
  );
}
