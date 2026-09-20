/**
 * StatsBar — trust stats strip. Dark slate variant for hero-adjacent placement.
 * Props: { variant?: "dark" | "light", stats? }
 */
const DEFAULT_STATS = [
  { value: "120+", label: "Projects Completed" },
  { value: "15", label: "Years in Business" },
  { value: "98%", label: "On-Time Handover" },
  { value: "$45M", label: "Build Value Delivered" },
];

export default function StatsBar({ variant = "dark", stats = DEFAULT_STATS }) {
  const bg = variant === "dark" ? "var(--bt-slate-900)" : "var(--bt-white)";
  return (
    <section
      aria-label="Company track record"
      style={{ background: bg, padding: "2.5rem 0", borderTop: "4px solid var(--bt-orange)" }}
    >
      <div className="bt-container">
        <div className={`bt-stats-strip ${variant}`}>
          {stats.map((s) => (
            <div key={s.label}>
              <div className="bt-stat-value">{s.value}</div>
              <div className="bt-stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
