import { useEffect, useState } from "react";
import Badge from "./components/Badge";
import LeadInput from "./components/LeadInput";
import StepTrail from "./components/StepTrail";
import ResultsPanel from "./components/ResultsPanel";
import { fetchExamples, fetchHealth, processLeadStream } from "./api";
import type { ExampleLead, HealthStatus, LeadResult, StepEvent } from "./types";

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [examples, setExamples] = useState<ExampleLead[]>([]);
  const [rawText, setRawText] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [steps, setSteps] = useState<StepEvent[]>([]);
  const [activeLabel, setActiveLabel] = useState<{ node: string; label: string } | null>(null);
  const [result, setResult] = useState<LeadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
    fetchExamples().then(setExamples).catch(() => setExamples([]));
  }, []);

  async function handleSubmit() {
    if (rawText.trim().length < 5 || isRunning) return;
    setIsRunning(true);
    setSteps([]);
    setActiveLabel(null);
    setResult(null);
    setError(null);

    await processLeadStream(rawText, {
      onStart: (node, label) => setActiveLabel({ node, label }),
      onStep: (step) => {
        setSteps((prev) => [...prev, step]);
        setActiveLabel(null);
      },
      onDone: (res) => {
        setResult(res);
        setIsRunning(false);
        setActiveLabel(null);
      },
      onError: (message) => {
        setError(message);
        setIsRunning(false);
        setActiveLabel(null);
      },
    });
  }

  return (
    <>
      <header className="site-header">
        <div className="site-header-inner">
          <div className="brand">
            <span className="brand-mark">🛫</span>
            LeadPilot
          </div>
          <div className="header-meta">
            <span>LangGraph agent · Gemini · FastAPI + React</span>
          </div>
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <div className="eyebrow">● AI Lead Intake Agent</div>
          <h1>
            An agent that turns a raw lead into <span>logged, drafted, notified</span>
          </h1>
          <p>
            Paste a raw inquiry — an email, a contact-form message, a DM. The agent extracts the
            structured details, logs it to a Sheet, drafts a personalized reply, and notifies
            Slack — all in one pass, no human steering the middle steps.
          </p>
          {health && (
            <div className="mode-strip">
              <Badge mode={health.llm_mode} label="Extraction" />
              <Badge mode={health.sheets_mode} label="Sheets" />
              <Badge mode={health.slack_mode} label="Slack" />
            </div>
          )}
        </section>

        <LeadInput
          value={rawText}
          onChange={setRawText}
          examples={examples}
          onPickExample={(text) => setRawText(text)}
          onSubmit={handleSubmit}
          isRunning={isRunning}
        />

        {error && <div className="error-banner">⚠ {error}</div>}

        <div className="workspace">
          <div className="panel">
            <div className="trail-title">Agent trail</div>
            <StepTrail steps={steps} activeLabel={activeLabel} isRunning={isRunning} />
          </div>

          <div>
            {result ? (
              <ResultsPanel result={result} />
            ) : (
              <div className="panel" style={{ minHeight: 160, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: "var(--text-faint)", fontSize: 13.5 }}>
                  Results will appear here once the agent finishes.
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="how-it-works">
          <strong>How this works:</strong> this demo runs against a sandboxed Sheet and Slack
          channel so visitors don't need to connect their own accounts. For a client, the exact
          same LangGraph pipeline points at their real CRM, inbox, and Slack workspace instead —
          the agent logic doesn't change, only the destinations do. When "demo mode" shows above,
          it means no live credentials are configured for that step; the agent still runs the
          full flow and shows exactly what would happen.
        </div>

        <footer className="site-footer">
          <div className="stack-line">
            <span>LangGraph</span> · <span>Gemini</span> · <span>FastAPI</span> · <span>React</span> ·{" "}
            <span>Google Sheets API</span> · <span>Slack</span>
          </div>
          <div>Built by Dileep Kumar Panchumarthi</div>
        </footer>
      </main>
    </>
  );
}
