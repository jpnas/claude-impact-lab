import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        rio: {
          night: "#050816",
          navy: "#0b1229",
          panel: "#101a3d",
          cyan: "#22d3ee",
          purple: "#8b5cf6"
        }
      },
      boxShadow: {
        glow: "0 0 40px rgba(34, 211, 238, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;
