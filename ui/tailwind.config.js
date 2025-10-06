/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // SCOUT Brand Colors - STM Brand Palette
        scout: {
          blue: '#1A5276',     // Primary brand blue (SINGLE)
          green: '#6B8F71',    // Success/Normal state (THROW)
          gray: '#6E6F71',     // Neutral/Supporting (MARKETING)
          yellow: '#f59e0b',   // Warning state (anomaly alerts)
          red: '#ef4444',      // Critical alert state
          dark: '#1e293b',     // Dark navy for headers
          light: '#f8fafc',    // Light background
        },
        // shadcn/ui design tokens
        border: "hsl(214.3 31.8% 91.4%)",
        input: "hsl(214.3 31.8% 91.4%)",
        ring: "hsl(222.2 84% 4.9%)",
        background: "hsl(0 0% 100%)",
        foreground: "hsl(222.2 84% 4.9%)",
        primary: {
          DEFAULT: "#1A5276",  // STM Blue
          foreground: "hsl(210 40% 98%)",
        },
        secondary: {
          DEFAULT: "hsl(210 40% 96.1%)",
          foreground: "hsl(222.2 47.4% 11.2%)",
        },
        muted: {
          DEFAULT: "hsl(210 40% 96.1%)",
          foreground: "hsl(215.4 16.3% 46.9%)",
        },
        accent: {
          DEFAULT: "#6B8F71",  // STM Green
          foreground: "hsl(222.2 47.4% 11.2%)",
        },
      },
      borderRadius: {
        lg: "0.5rem",
        md: "calc(0.5rem - 2px)",
        sm: "calc(0.5rem - 4px)",
      },
    },
  },
  plugins: [],
}
