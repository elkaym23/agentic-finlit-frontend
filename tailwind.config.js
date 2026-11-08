/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Outfit", "system-ui", "sans-serif"] },
      colors: {
        ink: { DEFAULT: "#1d1b2c", soft: "#4b4863", mute: "#8b88a3" },
        // Jamaica: green, gold, black
        jam: { green: "#009b3a", leaf: "#00b347", gold: "#fed100", sun: "#ffc400", black: "#111111" },
        tile: {
          mint: "#dcf5e4", sun: "#fff3c4", peach: "#ffe4d6", lilac: "#ece6ff",
          sky: "#dff0ff", rose: "#ffe1ec", sand: "#f6efe3",
        },
      },
      borderRadius: { "4xl": "2rem", "5xl": "2.5rem" },
      boxShadow: {
        card: "0 1px 2px rgba(29,27,44,.04), 0 8px 24px rgba(29,27,44,.06)",
        float: "0 20px 60px rgba(80,70,160,.18)",
      },
      keyframes: {
        pop: { "0%": { transform: "scale(.9)", opacity: "0" }, "100%": { transform: "scale(1)", opacity: "1" } },
        bob: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-6px)" } },
        flap: { "0%,100%": { transform: "rotate(-8deg)" }, "50%": { transform: "rotate(14deg)" } },
      },
      animation: { pop: "pop .25s ease-out", bob: "bob 3s ease-in-out infinite", flap: "flap .25s ease-in-out infinite" },
    },
  },
  plugins: [],
};
