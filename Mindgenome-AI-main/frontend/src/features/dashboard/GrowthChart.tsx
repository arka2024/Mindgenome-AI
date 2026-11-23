import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function GrowthChart({ data }: { data: Array<{ date: string; mastery: number }> }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-48 w-full items-center justify-center text-xs text-muted">
        No growth data recorded yet. Complete quizzes to track your velocity.
      </div>
    );
  }

  return (
    <div className="h-52 w-full pt-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 15, left: -20, bottom: 5 }}>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "var(--mg-muted)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--mg-line)" }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: "var(--mg-muted)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--mg-line)" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--mg-surface)",
              borderColor: "var(--mg-line)",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
              fontSize: "12px",
            }}
            formatter={(val: number) => [`${Math.round(val)}% Mastery`, "Overall"]}
          />
          <Line
            type="monotone"
            dataKey="mastery"
            stroke="var(--mg-helix)"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "var(--mg-helix)" }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
