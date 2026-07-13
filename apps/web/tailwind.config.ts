import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        boe: {
          ink: "#1a1a2e",
          primary: "#c0392b", // rojo BOE
          accent: "#2c5282",
        },
      },
    },
  },
  plugins: [],
};

export default config;
