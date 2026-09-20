import { services } from "../data/services";

/**
 * ServicesDetail — alternating image/text rows for /services page.
 * Props: { items? } defaults to services.js data.
 */
export default function ServicesDetail({ items = services }) {
  return (
    <section className="bt-section" aria-label="Service details">
      <div className="bt-container" style={{ display: "grid", gap: "2.5rem" }}>
        {items.map((s, i) => (
          <article
            key={s.slug}
            className="bt-card"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              alignItems: "stretch",
            }}
          >
            <div
              aria-hidden="true"
              style={{
                background: `linear-gradient(rgba(26,36,48,.25), rgba(26,36,48,.45)), var(--bt-slate-100)`,
                minHeight: "220px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "3rem",
                order: i % 2 === 1 ? 2 : 0,
              }}
            >
              <span role="img" aria-label={s.title}>
                {s.icon}
              </span>
            </div>
            <div style={{ padding: "2rem" }}>
              <span className="bt-badge">{s.priceFrom}</span>
              <h3 style={{ marginTop: "0.75rem" }}>{s.title}</h3>
              <p>{s.description}</p>
              <ul style={{ paddingLeft: "1.2rem", margin: "0 0 1.25rem" }}>
                {s.bullets.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <a href="/quote" className="bt-btn-dark" data-analytics="cta_quote_click">
                  Get Free Quote
                </a>
                <span style={{ fontSize: "0.85rem", color: "var(--bt-slate-500)", alignSelf: "center" }}>
                  ⏱ {s.timeline}
                </span>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
