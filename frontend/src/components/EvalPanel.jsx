import { Bar, BarChart, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Card from "./Card.jsx";
import { MODE_LABEL } from "../labels.js";

// `data` is the JSON from GET /api/eval/latest (your teammate's App fetches it and passes it in).
export default function EvalPanel({ data }) {
  if (!data) {
    return (
      <Card title="Evaluation">
        <p className="text-sm text-slate-500">No evaluation results yet.</p>
      </Card>
    );
  }
  const arms = Object.entries(data.arms);
  const chart = arms.map(([arm, s]) => ({
    arm: MODE_LABEL[arm] || arm,
    cost: s.mean_cost,
    accuracy: Math.round(s.accuracy * 100),
  }));
  const llm = data.config.llm_mode === "nemotron" ? `Nemotron (${data.config.model})` : "MOCK LLM, not Nemotron";

  return (
    <Card title={`Evaluation: ${data.n_seeds} hidden-fault scenarios`} subtitle={`${data.seed_file} · ${llm} · ${data.generated_at}`}>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-slate-500">
              <tr>
                <th className="py-1 font-normal">Investigator</th>
                <th className="font-normal">Accuracy</th>
                <th className="font-normal">Mean tests</th>
                <th className="font-normal">Mean cost</th>
                <th className="font-normal">Cost / correct</th>
                <th className="font-normal">Fallback</th>
              </tr>
            </thead>
            <tbody className="text-slate-200">
              {arms.map(([arm, s]) => (
                <tr key={arm} className="border-t border-slate-800">
                  <td className="py-1.5">{MODE_LABEL[arm] || arm}</td>
                  <td>{(s.accuracy * 100).toFixed(1)}%</td>
                  <td>{s.mean_tests}</td>
                  <td>{s.mean_cost}</td>
                  <td>{s.cost_per_correct}</td>
                  <td>{(s.fallback_rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart} margin={{ left: -10 }}>
              <XAxis dataKey="arm" tick={{ fill: "#94a3b8", fontSize: 10 }} interval={0} />
              <YAxis yAxisId="cost" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis yAxisId="acc" orientation="right" domain={[0, 100]} unit="%" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar yAxisId="cost" dataKey="cost" name="Mean test cost" fill="#84cc16" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="acc" dataKey="accuracy" name="Accuracy %" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  );
}