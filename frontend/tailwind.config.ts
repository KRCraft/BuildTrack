import type { Config } from "tailwindcss";
export default { content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}", "./lib/**/*.{js,ts,jsx,tsx}", "./src/**/*.{js,jsx,ts,tsx}"], theme: { extend: { colors: { ink: "#15211d", moss: "#1f6d54", sand: "#f6f5f0", clay: "#d36d43" }, boxShadow: { panel: "0 16px 38px rgba(19, 34, 28, .08)" } } }, plugins: [] } satisfies Config;
