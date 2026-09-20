/**
 * BuildTrack services catalog — single source for Services grid + detail + quote form select.
 */
export const services = [
  {
    slug: "custom-homes",
    icon: "🏠",
    title: "Custom Homes",
    tagline: "Architect-designed, fixed-price new builds",
    description:
      "Turnkey custom homes from slab to handover with a fixed quote, 10-year structural warranty, and daily photo updates.",
    bullets: ["Fixed-price contract", "Energy-efficient standard", "10-yr structural warranty"],
    priceFrom: "From $280k",
    timeline: "6–10 months",
  },
  {
    slug: "renovations",
    icon: "🔨",
    title: "Renovations & Extensions",
    tagline: "Live-in friendly remodels",
    description:
      "Second stories, extensions, and whole-home remodels with dust control and a livable-site plan.",
    bullets: ["Live-in phasing plan", "Council approvals handled", "3D design preview"],
    priceFrom: "From $45k",
    timeline: "4–16 weeks",
  },
  {
    slug: "commercial",
    icon: "🏢",
    title: "Commercial Fit-Outs",
    tagline: "Retail, hospitality & clinics",
    description:
      "After-hours and staged works so you keep trading. Compliance, accessibility, and landlord approvals covered.",
    bullets: ["After-hours available", "Compliance & permits", "Fast-track programs"],
    priceFrom: "Custom quote",
    timeline: "4–14 weeks",
  },
  {
    slug: "roofing",
    icon: "🏗️",
    title: "Roofing & Cladding",
    tagline: "Repairs to full replacements",
    description:
      "Metal, tile, and membrane roofing with leak diagnostics, insulation upgrades, and 15-year workmanship cover.",
    bullets: ["Free roof inspection", "Storm-damage repairs", "Gutter & fascia included"],
    priceFrom: "From $12k",
    timeline: "1–3 weeks",
  },
  {
    slug: "kitchen-bath",
    icon: "🛁",
    title: "Kitchens & Bathrooms",
    tagline: "High-impact rooms, fast turnaround",
    description:
      "Custom cabinetry, stone tops, and quality fixtures — most kitchens done in 4–6 weeks.",
    bullets: ["In-house joinery", "Stone & tile showroom", "Plumbing + electrical licensed"],
    priceFrom: "From $18k",
    timeline: "3–6 weeks",
  },
  {
    slug: "project-tracking",
    icon: "📊",
    title: "BuildTrack Progress Portal",
    tagline: "Free with every build",
    description:
      "Every client gets daily photos, cost tracker, schedule, and direct chat with your site manager.",
    bullets: ["Daily photo feed", "Live budget tracker", "Direct builder chat"],
    priceFrom: "Included free",
    timeline: "Every project",
  },
];

export const serviceOptions = services.map((s) => ({ value: s.slug, label: s.title }));

export default services;
