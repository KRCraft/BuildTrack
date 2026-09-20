/**
 * CTASection — reusable orange call-to-action band.
 * Props: { headline?, sub?, primaryLabel?, phone? }
 */
export default function CTASection({
  headline = "Ready to Start? Get Your Free Fixed Quote in 48 Hours.",
  sub = "No obligation. A licensed builder will call you back within one business day.",
  primaryLabel = "Get Free Quote",
  phone = "(555) 123-4567",
}) {
  return (
    <section
      aria-label="Get a free quote"
      style={{ background: "var(--bt-orange)", padding: "3.5rem 0" }}
    >
      <div
        className="bt-container"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "1.5rem",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ maxWidth: "34rem" }}>
          <h2 style={{ color: "#1A2430", marginBottom: "0.5rem" }}>{headline}</h2>
          <p style={{ color: "rgba(26,36,48,.85)", margin: 0 }}>{sub}</p>
        </div>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <a href="/quote" className="bt-btn-dark" data-analytics="cta_quote_click">
            {primaryLabel} →
          </a>
          <a
            href={`tel:${phone.replace(/[^+\d]/g, "")}`}
            style={{
              display: "inline-flex",
              alignItems: "center",
              fontWeight: 700,
              color: "#1A2430",
              textDecoration: "none",
              border: "2px solid #1A2430",
              borderRadius: "8px",
              padding: "0.75rem 1.5rem",
            }}
          >
            ☎ {phone}
          </a>
        </div>
      </div>
    </section>
  );
}
