/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ["Inter", "sans-serif"],
      },
      colors: {
        // Core sustainability + metal palette (updated brown-centric scheme)
        // Adjusted to warmer tones for cohesive brand look; keys retained for backwards compatibility.
        "brand-copper": "#A95E2F", // Primary Copper (slightly deeper for contrast)
        "brand-steel": "#6B625B", // Warm steel / muted brown-gray
        "brand-aluminum": "#D6D1CC", // Soft warm metal neutral
        "brand-blue": "#4A2E18", // Deep brown (formerly mineral blue key)
        "brand-green": "#8C5A32", // Repurposed as supportive accent (legacy key)
        "brand-charcoal": "#1F1A18", // Slightly warmer charcoal
        "brand-soft": "#FFF7F1", // Warm soft background
        "brand-gold": "#C98E3B", // Muted gold for highlights
        // Legacy mappings (kept for backward compatibility in components)
        "brand-emerald": "#3FA34D",
        "brand-forest": "#59391c",
        "brand-sky": "#F9FAFB",
        "accent-sun": "#DAA520",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.8" },
          "50%": { opacity: "0.4" },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
