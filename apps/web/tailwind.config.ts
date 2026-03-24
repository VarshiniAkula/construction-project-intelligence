import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Construction-themed palette
        hard: {
          hat: "#E87722",       // Safety orange - primary accent
          steel: "#4A6FA5",     // Steel blue - secondary
          concrete: "#8B8B8B",  // Concrete gray
          slate: "#2D3748",     // Charcoal slate
          beam: "#1A202C",      // Dark steel
        },
        surface: {
          DEFAULT: "#F7F8FA",
          paper: "#FFFFFF",
          muted: "#EDF0F4",
          border: "#D1D5DB",
        },
        status: {
          approved: "#16A34A",
          pending: "#D97706",
          rejected: "#DC2626",
          processing: "#2563EB",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
export default config;
