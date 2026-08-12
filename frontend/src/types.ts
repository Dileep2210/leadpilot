export interface StructuredLead {
  name: string | null;
  company: string | null;
  contact: string | null;
  need: string | null;
  urgency: "hot" | "warm" | "cold" | "unknown";
  budget_hint: string | null;
}

export interface SheetResult {
  mode: "live" | "mock";
  row_number: number | null;
  sheet_url: string | null;
  note: string | null;
}

export interface SlackResult {
  mode: "live" | "mock";
  posted: boolean;
  message: string;
  note: string | null;
}

export interface StepEvent {
  node: string;
  label: string;
  output: Record<string, unknown>;
}

export interface LeadResult {
  raw_text: string;
  structured: StructuredLead;
  sheet: SheetResult;
  draft_reply: string;
  slack: SlackResult;
}

export interface ExampleLead {
  label: string;
  text: string;
}

export interface HealthStatus {
  status: string;
  llm_mode: "live" | "mock";
  sheets_mode: "live" | "mock";
  slack_mode: "live" | "mock";
}
