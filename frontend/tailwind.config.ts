import type { Config } from "tailwindcss";
export default {
  darkMode: ["class"],
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}", "./lib/**/*.{js,ts,jsx,tsx}", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#15211d",
        moss: "#1f6d54",
        "moss-dark": "#175641",
        sand: "#f6f5f0",
        clay: "#d36d43",
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
      },
      boxShadow: { panel: "0 16px 38px rgba(19, 34, 28, .08)", soft: "0 4px 16px rgba(26,36,48,.08)", large: "0 12px 32px rgba(26,36,48,.14)" },
      borderRadius: { xl: "16px", "2xl": "20px" },
      fontFamily: { display: ["Archivo", "Inter", "system-ui", "sans-serif"], body: ["Inter", "system-ui", "sans-serif"] },
      keyframes: {
        shimmer: { "0%": { transform: "translateX(-100%)" }, "100%": { transform: "translateX(100%)" } },
        fadeIn: { "0%": { opacity: "0", transform: "translateY(4px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
      },
      animation: { shimmer: "shimmer 1.5s infinite", fadeIn: "fadeIn 0.3s ease-out" },
    },
  },
  plugins: [],
} satisfies Config;
