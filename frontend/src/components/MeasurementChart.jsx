import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Card from "./Card.jsx";

// Per-GPU tools: one bar per GPU, the most extreme GPU highlighted, a line where "worrying" starts.
const PER_GPU = {
  check_thermals: { key: "temps_c", unit: "°C", color: "#f97316", limit: 85, limitLabel: "throttle zone" },
  check_memory: { key: "mem_used_pct", unit: "%", color: "#a855f7", limit: 95, limitLabel: "near full" },
  check_power: { key: "power_w", unit: " W", color: "#eab308", limit: null, limitLabel: "" },
};

// Single-number tools: the value next to a "normal" reference line.
const SINGLE = {
  run_nccl_bandwidth_test: { key: "busbw_gbps", label: "Bus bandwidth", unit: " GB/s", normal: 165, max: 200 },
  run_gpu_stress_test: { key: "sustained_clock_drop_pct", label: "Clock drop under load", unit: "%", normal: 10, max: 50 },
};

const tooltipStyle = { background: "#0f172a", border: "1px solid #334155" };

function PerGpuChart({ values, spec }) {
  const maxIdx = values.indexOf(Math.max(...values));
  const data = values.map((v, i) => ({ gpu: `GPU${i}`, value: v }));
  return (
    <div className="h-44">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="gpu" tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit={spec.unit} />
          <Tooltip formatter={(v) => `${v}${spec.unit}`} contentStyle={tooltipStyle} />
          {spec.limit && (
            <ReferenceLine
              y={spec.limit}
              stroke="#f43f5e"
              strokeDasharray="4 4"
              label={{ value: spec.limitLabel, fill: "#f43f5e", fontSize: 10, position: "insideTopRight" }}
            />
          )}
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={d.gpu} fill={spec.color} fillOpacity={i === maxIdx ? 1 : 0.35} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function SingleValueChart({ value, spec }) {
  const data = [{ name: spec.label, value }];
  return (
    <div className="h-28">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
          <XAxis type="number" domain={[0, spec.max]} unit={spec.unit} tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={130} tick={{ fill: "#cbd5e1", fontSize: 12 }} />
          <Tooltip formatter={(v) => `${v}${spec.unit}`} contentStyle={tooltipStyle} />
          <ReferenceLine
            x={spec.normal}
            stroke="#84cc16"
            strokeDasharray="4 4"
            label={{ value: `normal ${spec.normal}${spec.unit}`, fill: "#84cc16", fontSize: 10, position: "top" }}
          />
          <Bar dataKey="value" fill="#38bdf8" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function MeasurementChart({ step }) {
  if (!step) {
    return (
      <Card title="Measurements">
        <p className="text-sm text-slate-500">Waiting for the first test…</p>
      </Card>
    );
  }
  const perGpu = PER_GPU[step.tool];
  const single = SINGLE[step.tool];
  return (
    <Card title={`Result ${step.result_id}: ${step.tool}`} subtitle={step.summary}>
      {perGpu && <PerGpuChart values={step.measurements[perGpu.key]} spec={perGpu} />}
      {single && <SingleValueChart value={step.measurements[single.key]} spec={single} />}
      {!perGpu && !single && (
        <dl className="grid grid-cols-2 gap-2">
          {Object.entries(step.measurements).map(([k, v]) => (
            <div key={k} className="rounded-lg bg-slate-800/60 p-2">
              <dt className="text-xs text-slate-500">{k.split("_").join(" ")}</dt>
              <dd className="font-mono text-sm text-slate-100">{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}
      {step.observation && (
        <p className="mt-2 text-xs text-slate-500">
          Evidence label: <span className="font-mono text-slate-300">{step.observation}</span>
        </p>
      )}
    </Card>
  );
}