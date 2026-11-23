/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--mg-canvas)",
        surface: "var(--mg-surface)",
        ink: "var(--mg-ink)",
        muted: "var(--mg-muted)",
        line: "var(--mg-line)",
        helix: "var(--mg-helix)",
        copper: "var(--mg-copper)",
        danger: "var(--mg-danger)",
        beginner: "var(--mg-beginner)",
        developing: "var(--mg-developing)",
        proficient: "var(--mg-proficient)",
        mastered: "var(--mg-mastered)",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Source Sans 3", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 10px 30px -18px rgb(184 107 61 / 0.28)",
      },
      borderRadius: {
        control: "6px",
        card: "12px",
        sheet: "20px",
      },
    },
  },
  plugins: [],
};
