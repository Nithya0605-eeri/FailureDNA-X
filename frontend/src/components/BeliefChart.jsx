import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Card from "./Card.jsx";
import { FAULTS, FAULT_COLOR, FAULT_LABEL } from "../labels.js";

export default function BeliefChart({ beliefs, truth, threshold }) {
  const data = FAULTS.map((f) => ({
    key: f,
    name: FAULT_LABEL[f],
    value: Math.round((beliefs[f] || 0) * 1000) / 10,
  }));
  return (
    <Card title="Current beliefs" subtitle={`Probability of each cause · stop threshold ${Math.round(threshold * 100)}%`}>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
            <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={130} tick={{ fill: "#cbd5e1", fontSize: 12 }} />
            <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            <ReferenceLine x={threshold * 100} stroke="#64748b" strokeDasharray="4 4" />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {data.map((d) => (
                <Cell
                  key={d.key}
                  fill={FAULT_COLOR[d.key]}
                  stroke={truth && truth.fault === d.key ? "#f8fafc" : "none"}
                  strokeWidth={2}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      {truth && <p className="mt-2 text-xs text-slate-400">White outline = the hidden fault, revealed after the diagnosis.</p>}
    </Card>
  );
}