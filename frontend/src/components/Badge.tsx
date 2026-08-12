interface Props {
  mode: "live" | "mock";
  label: string;
}

export default function Badge({ mode, label }: Props) {
  return (
    <span className={`badge ${mode === "live" ? "badge-live" : "badge-mock"}`}>
      <span className="badge-dot" />
      {label}: {mode === "live" ? "live" : "demo mode"}
    </span>
  );
}
