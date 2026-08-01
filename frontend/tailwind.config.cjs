/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#e0f7f1",
          100: "#b3ebdc",
          200: "#80dfc3",
          300: "#4dd3aa",
          400: "#26c995",
          500: "#00bf80",
          600: "#00aa73",
          700: "#009364",
          800: "#007c55",
          900: "#006645",
        },
        accent: {
          500: "#ffb400",
        },
        success: {
          500: "#10B981",
        },
        warning: {
          500: "#F59E0B",
        },
        danger: {
          500: "#EF4444",
        },
        background: {
          500: "#F8FAFC",
        },
        dark: {
          500: "#111827",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
