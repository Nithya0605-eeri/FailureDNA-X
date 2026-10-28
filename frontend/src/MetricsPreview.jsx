// A page with SAMPLE data so you can build the charts without the backend.
// Open http://localhost:5173/?preview  (your teammate's real App is unaffected).
import { useState } from "react";
import BeliefChart from "./components/BeliefChart.jsx";
import BeliefHistory from "./components/BeliefHistory.jsx";
import EvalPanel from "./components/EvalPanel.jsx";
import MeasurementChart from "./components/MeasurementChart.jsx";

const B = (t, m, n, f) => ({ thermal_throttling: t, memory_pressure: m, network_congestion: n, no_fault: f });

const SAMPLE_STEPS = [
  { result_id: "r1", tool: "get_job_summary", summary: "Step time 1.84x baseline, variability (CV) 0.04, avg utilization 52.1%.",
    measurements: { step_time_ratio: 1.84, step_time_cv: 0.04, gpu_util_pct: 52.1 }, observation: "large|steady",
    beliefs_after: B(0.47, 0.0, 0.42, 0.11) },
  { result_id: "r2", tool: "check_thermals", summary: "Hottest GPU2 at 91.2C, clock 1402 MHz; thermal throttle active on GPUs [2].",
    measurements: { temps_c: [64.1, 66.3, 91.2, 62.8], sm_clock_mhz: [1950, 1961, 1402, 1971], throttle_thermal: [false, false, true, false] },
    observation: "hot|throttle", beliefs_after: B(0.97, 0.0, 0.02, 0.01) },
  { result_id: "r3", tool: "check_memory", summary: "Highest memory use GPU1 at 81.4%; max allocator retries 2.",
    measurements: { mem_used_pct: [72.5, 81.4, 66.0, 70.2], alloc_retries: [1, 2, 0, 1] }, observation: "ok|no_retries",
    beliefs_after: B(0.98, 0.0, 0.01, 0.01) },
  { result_id: "r4", tool: "run_nccl_bandwidth_test", summary: "All-reduce bus bandwidth 171.3 GB/s, latency 9.8 ms.",
    measurements: { busbw_gbps: 171.3, allreduce_ms: 9.8 }, observation: "normal|fast_allreduce", beliefs_after: B(0.99, 0.0, 0.0, 0.01) },
  { result_id: "r5", tool: "run_gpu_stress_test", summary: "Under sustained load GPU2 lost 31.5% clock, peaking at 101.5C.",
    measurements: { sustained_clock_drop_pct: 31.5, worst_gpu: 2, peak_temp_c: 101.5 }, observation: "collapsing",
    beliefs_after: B(1.0, 0.0, 0.0, 0.0) },
];

const SAMPLE_EVAL = {
  seed_file: "seeds/test.txt (SAMPLE NUMBERS)", n_seeds: 48, generated_at: "sample",
  config: { llm_mode: "mock_llm", model: null },
  arms: {
    fixed: { accuracy: 0.9, mean_tests: 6, mean_cost: 18, cost_per_correct: 20.1, fallback_rate: 0 },
    fixed_early: { accuracy: 0.9, mean_tests: 4.0, mean_cost: 8.5, cost_per_correct: 9.5, fallback_rate: 0 },
    infogain: { accuracy: 0.9, mean_tests: 3.6, mean_cost: 7.5, cost_per_correct: 8.4, fallback_rate: 0 },
    nemotron: { accuracy: 0.9, mean_tests: 3.5, mean_cost: 7.0, cost_per_correct: 7.8, fallback_rate: 0.02 },
  },
};

export default function MetricsPreview() {
  const [n, setN] = useState(2); // how many steps have "happened"
  const steps = SAMPLE_STEPS.slice(0, n);
  const last = steps[steps.length - 1];
  const done = n === SAMPLE_STEPS.length;
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6 text-slate-100">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold">Metrics preview (sample data)</h1>
        <button className="rounded bg-slate-700 px-3 py-1 text-sm" onClick={() => setN(Math.max(0, n - 1))}>◀ step</button>
        <button className="rounded bg-slate-700 px-3 py-1 text-sm" onClick={() => setN(Math.min(SAMPLE_STEPS.length, n + 1))}>step ▶</button>
        <span className="text-sm text-slate-400">{n} / {SAMPLE_STEPS.length} tests</span>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <BeliefChart beliefs={last ? last.beliefs_after : B(0.25, 0.25, 0.25, 0.25)}
                     truth={done ? { fault: "thermal_throttling" } : null} threshold={0.9} />
        <BeliefHistory steps={steps} />
        <MeasurementChart step={last} />
      </div>
      <EvalPanel data={SAMPLE_EVAL} />
    </div>
  );
}