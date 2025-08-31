/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0a0c10",
        panel: "#0f1218",
        line: "#1b2330",
        accent: { teal: "#00e5a8", cyan: "#5ef1ff", lime: "#c2ff72" }
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(0,229,168,.25), 0 8px 40px -12px rgba(0,229,168,.25)"
      }
    },
  },
  plugins: [],
}
