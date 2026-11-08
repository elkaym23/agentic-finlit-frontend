// FinBuddy — a doctor bird (red-billed streamertail), Jamaica's national bird.
export default function Mascot({ size = 160, mood = "happy", className = "" }:
  { size?: number; mood?: "happy" | "think" | "cheer"; className?: string }) {
  return (
    <svg viewBox="0 0 220 200" width={size} height={(size * 200) / 220} className={className} role="img"
         aria-label="FinBuddy the doctor bird">
      {/* long tail streamers */}
      <path d="M78 128 C 52 160, 30 182, 6 196" stroke="#111" strokeWidth="7" fill="none" strokeLinecap="round" />
      <path d="M86 132 C 70 166, 58 186, 40 199" stroke="#1f2a24" strokeWidth="6" fill="none" strokeLinecap="round" />
      {/* body */}
      <ellipse cx="112" cy="108" rx="44" ry="36" fill="#00a443" transform="rotate(-18 112 108)" />
      <ellipse cx="122" cy="120" rx="26" ry="18" fill="#3fd17a" transform="rotate(-18 122 120)" />
      {/* wing */}
      <g style={{ transformOrigin: "104px 96px" }} className={mood === "cheer" ? "animate-flap" : ""}>
        <path d="M104 96 C 80 60, 60 52, 44 58 C 62 72, 74 96, 100 112 Z" fill="#007a32" />
        <path d="M98 100 C 82 80, 70 74, 58 74" stroke="#00a443" strokeWidth="3" fill="none" strokeLinecap="round" />
      </g>
      {/* head with black crest */}
      <circle cx="150" cy="72" r="26" fill="#111" />
      <path d="M128 60 C 120 44, 132 36, 140 48" fill="#111" />
      <path d="M150 92 C 160 96, 170 92, 172 84 C 162 88, 156 88, 150 92 Z" fill="#00a443" />
      {/* eye */}
      <circle cx="157" cy="68" r="9" fill="#fff" />
      <circle cx={mood === "think" ? 160 : 159} cy={mood === "think" ? 64 : 69} r="5" fill="#111" />
      <circle cx="161" cy="66" r="1.8" fill="#fff" />
      {mood !== "think" && <path d="M151 80 q 6 4 12 0" stroke="#fed100" strokeWidth="2.5" fill="none" strokeLinecap="round" />}
      {/* long red bill */}
      <path d="M173 74 L 214 82 L 174 80 Z" fill="#e5322d" />
      <path d="M210 81 L 216 82 L 210 83 Z" fill="#111" />
      {/* cheeks */}
      <circle cx="146" cy="82" r="4" fill="#ff7a8a" opacity=".55" />
      {/* gold coin it's holding */}
      <g transform="translate(118 140)">
        <circle r="15" fill="#fed100" stroke="#e0b400" strokeWidth="3" />
        <text textAnchor="middle" y="5" fontSize="13" fontWeight="800" fill="#7a5a00" fontFamily="Outfit, sans-serif">J$</text>
      </g>
      {/* feet */}
      <path d="M108 140 l -4 10 M118 142 l -2 10" stroke="#3b2b1a" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
