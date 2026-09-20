import testimonials from "../data/mockTestimonials";

/**
 * Testimonials — merge-safe standalone section.
 * Props: { items?, title?, subtitle? }
 * Usage: <Testimonials /> or <Testimonials items={...} />
 */
export default function Testimonials({ items = testimonials, title, subtitle }) {
  const heading = title || "Trusted by Homeowners & Businesses";
  const sub =
    subtitle || "4.9-star average from 200+ verified reviews. Fixed quotes, clean sites, on-time handover.";

  return (
    <section className="bt-section" aria-label="Customer testimonials">
      <div className="bt-container">
        <span className="bt-badge">★ 4.9 Rated</span>
        <h2 style={{ marginTop: "0.75rem" }}>{heading}</h2>
        <p style={{ maxWidth: "40rem" }}>{sub}</p>
        <div className="bt-grid-3" style={{ marginTop: "2rem" }}>
          {items.slice(0, 6).map((t) => (
            <article key={t.id} className="bt-card" style={{ padding: "1.5rem" }}>
              <div aria-label={`${t.rating} out of 5 stars`} style={{ color: "#F26A1B", letterSpacing: "2px" }}>
                {"★".repeat(t.rating)}
                {"☆".repeat(5 - t.rating)}
              </div>
              <p style={{ fontStyle: "italic", margin: "0.75rem 0" }}>&ldquo;{t.quote}&rdquo;</p>
              <footer>
                <strong style={{ color: "var(--bt-slate-900)" }}>{t.name}</strong>
                <div style={{ fontSize: "0.85rem", color: "var(--bt-slate-500)" }}>
                  {t.location} · {t.service}
                </div>
                {t.project && (
                  <div style={{ fontSize: "0.8rem", color: "var(--bt-success)", fontWeight: 600 }}>
                    ✓ {t.project}
                  </div>
                )}
              </footer>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
