import { Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Card from "./Card.jsx";
import { FAULTS, FAULT_COLOR, FAULT_LABEL } from "../labels.js";

export default function BeliefHistory({ steps }) {
  if (!steps || steps.length === 0) return null;
  const rows = [{ step: "start", ...Object.fromEntries(FAULTS.map((f) => [f, 25])) }];
  for (const s of steps) {
    rows.push({ step: s.result_id, ...Object.fromEntries(FAULTS.map((f) => [f, Math.round(s.beliefs_after[f] * 1000) / 10])) });
  }
  return (
    <Card title="How beliefs changed" subtitle="Probability of each cause after every test">
      <div className="h-52">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ left: -10, right: 10 }}>
            <XAxis dataKey="step" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis domain={[0, 100]} unit="%" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {FAULTS.map((f) => (
              <Line key={f} type="monotone" dataKey={f} name={FAULT_LABEL[f]} stroke={FAULT_COLOR[f]} strokeWidth={2} dot />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}