/**
 * Realistic mock projects for BuildTrack landing / portfolio.
 * Replace `image` paths once real photos are added (see assets README).
 */
export const mockProjects = [
  {
    id: "maple-custom-home",
    title: "Maple Street Custom Home",
    location: "Springfield",
    type: "Custom Home",
    status: "Completed",
    specs: { sqft: 2450, bedrooms: 4, baths: 3, duration: "7 months", value: "$485,000" },
    scope: ["Full architectural build", "Double garage", "Energy-efficient insulation"],
    image: "/images/projects/maple-home.jpg",
  },
  {
    id: "downtown-cafe-fitout",
    title: "Downtown Café Fit-Out",
    location: "Riverside District",
    type: "Commercial",
    status: "Completed",
    specs: { sqft: 1800, duration: "10 weeks", value: "$145,000" },
    scope: ["Commercial kitchen", "Custom joinery", "ADA compliance upgrade"],
    image: "/images/projects/cafe-fitout.jpg",
  },
  {
    id: "oak-renovation",
    title: "Oak Avenue Renovation + Extension",
    location: "Oakdale",
    type: "Renovation",
    status: "In Progress",
    specs: { sqft: 1200, duration: "14 weeks", value: "$128,000" },
    scope: ["Second-story extension", "Kitchen & bath remodel", "New roofing"],
    image: "/images/projects/oak-renovation.jpg",
  },
  {
    id: "lakeside-duplex",
    title: "Lakeside Duplex Pair",
    location: "Lakeview",
    type: "Custom Home",
    status: "Completed",
    specs: { sqft: 3200, bedrooms: 6, baths: 4, duration: "9 months", value: "$620,000" },
    scope: ["Dual occupancy", "Landscaping package", "Solar + battery"],
    image: "/images/projects/lakeside-duplex.jpg",
  },
  {
    id: "clinic-refurb",
    title: "Medical Clinic Refurbishment",
    location: "Northgate",
    type: "Commercial",
    status: "Completed",
    specs: { sqft: 2500, duration: "12 weeks", value: "$210,000" },
    scope: ["Sterile fit-out", "Acoustic treatment", "After-hours works"],
    image: "/images/projects/clinic-refurb.jpg",
  },
  {
    id: "cedar-kitchen",
    title: "Cedar Lane Kitchen & Bath",
    location: "Springfield",
    type: "Renovation",
    status: "Completed",
    specs: { sqft: 450, duration: "5 weeks", value: "$42,000" },
    scope: ["Custom cabinetry", "Stone benchtops", "Tiling + fixtures"],
    image: "/images/projects/cedar-kitchen.jpg",
  },
];

export default mockProjects;
