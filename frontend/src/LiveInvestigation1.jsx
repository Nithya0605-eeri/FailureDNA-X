// Live investigation page: runs a REAL hidden-fault investigation through /api/sim and shows the charts.
// Open http://localhost:5173/?live  (needs the backend running on port 8000).
import { useEffect, useRef, useState } from "react";
import BeliefChart from "./components/BeliefChart.jsx";
import BeliefHistory from "./components/BeliefHistory.jsx";
import Card from "./components/Card.jsx";
import MeasurementChart from "./components/MeasurementChart.jsx";
import { FAULT_LABEL, pct } from "./labels.js";

const API = "http://localhost:8000/api/sim";
const STEP_DELAY_MS = 800;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function call(path, options = {}) {
  const res = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}

const SOURCE_STYLE = {
  nemotron: "bg-lime-500/20 text-lime-300",
  mock_llm: "bg-amber-500/20 text-amber-300",
  fallback: "bg-rose-500/20 text-rose-300",
  infogain: "bg-sky-500/20 text-sky-300",
  fixed: "bg-slate-500/20 text-slate-300",
};

export default function LiveInvestigation1() {
  const [info, setInfo] = useState(null);
  const [mode, setMode] = useState("nemotron");
  const [inv, setInv] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const runId = useRef(0);

  useEffect(() => {
    call("/info").then(setInfo).catch(() => setError("Cannot reach the backend. Is uvicorn running on port 8000?"));
  }, []);

  async function inject() {
    const me = ++runId.current;
    setError("");
    setRunning(true);
    try {
      let state = await call("/investigations", { method: "POST", body: JSON.stringify({ mode }) });
      setInv(state);
      while (state.status !== "complete" && me === runId.current) {
        await sleep(STEP_DELAY_MS);
        state = await call(`/investigations/${state.id}/step`, { method: "POST" });
        if (me === runId.current) setInv(state);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      if (me === runId.current) setRunning(false);
    }
  }

  const steps = inv ? inv.steps : [];
  const last = steps.length ? steps[steps.length - 1] : null;
  const done = inv && inv.status === "complete";

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6 text-slate-100">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">FailureDNA X · Live investigation</h1>
          <p className="text-sm text-slate-400">A hidden GPU fault is injected. The AI only sees the symptom and the tests it chooses.</p>
        </div>
        {info && (
          <span className={`rounded-full px-3 py-1 text-xs ${info.llm_mode === "nemotron" ? SOURCE_STYLE.nemotron : SOURCE_STYLE.mock_llm}`}>
            {info.llm_mode === "nemotron" ? `NVIDIA Nemotron via Nebius Token Factory · ${info.model}` : "Mock LLM (no API key)"}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={inject}
          disabled={running}
          className="rounded-lg bg-lime-500 px-5 py-2.5 font-semibold text-slate-950 disabled:opacity-50"
        >
          {running ? "Investigating…" : "Inject Hidden Failure"}
        </button>
        <select value={mode} onChange={(e) => setMode(e.target.value)} className="rounded-md bg-slate-800 px-2 py-2 text-sm">
          <option value="nemotron">Nemotron agent</option>
          <option value="infogain">Info-gain heuristic</option>
          <option value="fixed">Fixed checklist</option>
        </select>
        {inv && <span className="text-sm text-slate-400">Symptom: {inv.symptom}</span>}
      </div>

      {error && <div className="rounded-lg bg-rose-500/15 px-4 py-3 text-sm text-rose-200">{error}</div>}

      {inv && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card title="Tests run"><p className="text-2xl font-semibold">{inv.tests_run}{running ? "…" : ""}</p></Card>
            <Card title="Test cost"><p className="text-2xl font-semibold">{inv.total_cost} / {inv.max_cost}</p></Card>
            <Card title="Fallbacks"><p className="text-2xl font-semibold">{inv.fallbacks}</p></Card>
            <Card title="Status"><p className="text-2xl font-semibold">{done ? "Complete" : "Investigating"}</p></Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Investigation timeline" subtitle="Each test the AI chose, and why">
              {!steps.length && <p className="text-sm text-slate-500">Choosing the first test…</p>}
              <ol className="space-y-3">
                {steps.map((s) => (
                  <li key={s.result_id} className="rounded-lg border border-slate-800 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs text-slate-500">{s.result_id}</span>
                      <span className="font-mono text-sm font-semibold">{s.tool}</span>
                      <span className="text-xs text-slate-500">cost {s.cost}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${SOURCE_STYLE[s.source] || SOURCE_STYLE.fixed}`}>{s.source}</span>
                    </div>
                    {s.hypothesis && <p className="mt-1 text-sm text-slate-300"><span className="text-slate-500">Hypothesis: </span>{s.hypothesis}</p>}
                    {s.reason && <p className="mt-1 text-sm italic text-slate-300">“{s.reason}”</p>}
                    <p className="mt-1 text-sm text-slate-400">{s.summary}</p>
                  </li>
                ))}
              </ol>
            </Card>
            <div className="space-y-6">
              <BeliefChart beliefs={inv.beliefs} truth={inv.truth} threshold={inv.stop_threshold} />
              <BeliefHistory steps={steps} />
              <MeasurementChart step={last} />
            </div>
          </div>

          {done && (
            <Card title="Verdict">
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-xs uppercase text-slate-500">Diagnosis</p>
                  <p className="text-lg font-semibold">{FAULT_LABEL[inv.diagnosis.cause]}</p>
                  <p className="text-sm text-slate-400">Confidence {pct(inv.diagnosis.confidence)} · cites {inv.diagnosis.cited_result_ids.join(", ")}</p>
                  {inv.diagnosis.explanation && <p className="mt-1 text-sm text-slate-300">{inv.diagnosis.explanation}</p>}
                </div>
                <div>
                  <p className="text-xs uppercase text-slate-500">Hidden fault (revealed)</p>
                  <p className="text-lg font-semibold">
                    {FAULT_LABEL[inv.truth.fault]}{inv.truth.severity ? ` · ${inv.truth.severity}` : ""}
                  </p>
                  <p className={`mt-1 inline-block rounded-full px-3 py-1 text-sm font-semibold ${inv.correct ? "bg-lime-500/20 text-lime-300" : "bg-rose-500/20 text-rose-300"}`}>
                    {inv.correct ? "✓ Correct" : "✗ Incorrect"}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase text-slate-500">Versus fixed checklist (same scenario)</p>
                  {inv.baseline && (
                    <p className="mt-1 text-sm text-slate-300">
                      This run: {inv.tests_run} tests, cost {inv.total_cost}<br />
                      Fixed checklist: {inv.baseline.tests_run} tests, cost {inv.baseline.total_cost}
                      {inv.baseline.correct ? " (correct)" : " (incorrect)"}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-slate-500">One run is an example, not a benchmark.</p>
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}