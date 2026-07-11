import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(222 26% 7%)",
        foreground: "hsl(210 40% 96%)",
        card: "hsl(222 24% 10%)",
        border: "hsl(220 18% 20%)",
        muted: "hsl(218 13% 48%)",
        accent: "hsl(166 78% 46%)",
        danger: "hsl(0 72% 58%)"
      },
      borderRadius: {
        lg: "8px",
        md: "6px",
        sm: "4px"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

export default config;
