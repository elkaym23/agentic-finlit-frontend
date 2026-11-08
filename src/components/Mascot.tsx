import { useId } from "react";

// Casheous: a cartoon doctor bird (red-billed streamertail), Jamaica's national bird.
// Emerald scaled body, black cap and swept-back crest, bronze-gold wings, short red bill,
// and the two long black streamer tails.

/** One rounded feather pointing straight up from (0,0); rotate it into place. */
const feather = (len: number, w: number) =>
  `M0 0 C ${w} ${-len * 0.22}, ${w * 0.95} ${-len * 0.8}, 0 ${-len} C ${-w * 0.95} ${-len * 0.8}, ${-w} ${-len * 0.22}, 0 0 Z`;

function Wing({ x, y, outer, inner, len, flap, scales }:
  { x: number; y: number; outer: number[]; inner: number[]; len: number; flap: string; scales: string }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <g style={{ transformOrigin: "0 0" }} className={flap}>
        {outer.map((a, i) => (
          <path key={`o${a}`} d={feather(len, 14)} transform={`rotate(${a})`}
                fill={i % 2 ? "#a87a33" : "#bf9142"} stroke="#6e4f20" strokeWidth="1.4" />
        ))}
        {inner.map((a) => (
          <path key={`i${a}`} d={feather(len * 0.6, 12)} transform={`rotate(${a})`} fill="#dcb86c" stroke="#a8813a" strokeWidth="1.2" />
        ))}
        <ellipse cx="0" cy="0" rx="19" ry="14" fill="#0b8a3c" />
        <ellipse cx="0" cy="0" rx="19" ry="14" fill={`url(#${scales})`} />
      </g>
    </g>
  );
}

/** `face` crops to the head so it still reads at small sizes (chat avatars, logo). */
export default function Mascot({ size = 160, mood = "happy", className = "", face = false }:
  { size?: number; mood?: "happy" | "think" | "cheer"; className?: string; face?: boolean }) {
  const scales = `scales${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const flap = mood === "cheer" ? "animate-flap" : "";
  const look = mood === "think" ? -6 : 0;
  const [vw, vh] = face ? [150, 150] : [250, 260];
  return (
    <svg viewBox={face ? "94 22 150 150" : "0 0 250 260"} width={size} height={(size * vh) / vw} className={className} role="img"
         aria-label="Casheous the doctor bird">
      <defs>
        {/* iridescent emerald scales, like the real bird's feathers */}
        <pattern id={scales} width="9" height="7" patternUnits="userSpaceOnUse">
          <path d="M0 7 Q 4.5 0.5 9 7" fill="none" stroke="#06642b" strokeWidth="1.1" opacity=".55" />
          <path d="M2 5.5 Q 4.5 2.5 7 5.5" fill="none" stroke="#5be08a" strokeWidth=".9" opacity=".45" />
        </pattern>
      </defs>

      {/* two long, thin streamer tails with feathered edges */}
      {[["M86 170 C 62 204, 40 230, 8 254", 4.5], ["M94 174 C 84 208, 74 236, 58 258", 4]].map(([d, w]) => (
        <g key={d as string}>
          <path d={d as string} stroke="#1a1a1a" strokeWidth={(w as number) + 4} fill="none" strokeLinecap="round" strokeDasharray="1.5 4" opacity=".7" />
          <path d={d as string} stroke="#111" strokeWidth={w as number} fill="none" strokeLinecap="round" />
        </g>
      ))}

      {/* wings sit behind the body, spread wide like a hummingbird in flight */}
      <Wing x={106} y={126} outer={[-98, -80, -62, -44, -26]} inner={[-88, -64, -40]} len={88} flap={flap} scales={scales} />
      <Wing x={136} y={140} outer={[72, 90, 108, 126, 144]} inner={[82, 106, 130]} len={72} flap={flap} scales={scales} />

      {/* short dark tail fan */}
      <g transform="translate(92 166)">
        {[198, 218, 238].map((a) => (
          <path key={a} d={feather(26, 8)} transform={`rotate(${a})`} fill={a === 218 ? "#063f1c" : "#0b6b30"} />
        ))}
      </g>

      {/* small round body with emerald scales */}
      <ellipse cx="116" cy="148" rx="34" ry="29" fill="#0b8a3c" transform="rotate(-30 116 148)" />
      <ellipse cx="116" cy="148" rx="34" ry="29" fill={`url(#${scales})`} transform="rotate(-30 116 148)" />
      <ellipse cx="126" cy="156" rx="18" ry="14" fill="#1fbf5c" opacity=".55" transform="rotate(-30 126 156)" />
      <ellipse cx="100" cy="134" rx="10" ry="5" fill="#fff" opacity=".18" transform="rotate(-34 100 134)" />

      {/* tiny feet */}
      <path d="M116 174 l -2 8 M126 172 l 0 8" stroke="#2b1f14" strokeWidth="3.5" strokeLinecap="round" />

      {/* crest: black feathers swept back */}
      <path d={feather(40, 7)} transform="translate(122 82) rotate(-84)" fill="#111" />
      <path d={feather(46, 7)} transform="translate(126 73) rotate(-66)" fill="#1d1d1d" />
      <path d={feather(38, 6)} transform="translate(133 66) rotate(-48)" fill="#111" />

      {/* big head: black cap over a scaled emerald throat */}
      <circle cx="156" cy="94" r="42" fill="#111" />
      <path d="M118 110 Q 156 140 196 108 Q 194 130 160 136 Q 126 134 118 110 Z" fill="#0b8a3c" />
      <path d="M118 110 Q 156 140 196 108 Q 194 130 160 136 Q 126 134 118 110 Z" fill={`url(#${scales})`} />
      <ellipse cx="146" cy="122" rx="12" ry="5" fill="#3fd17a" opacity=".55" />
      <ellipse cx="140" cy="70" rx="12" ry="6" fill="#fff" opacity=".12" transform="rotate(-30 140 70)" />

      {/* short red bill with a black tip */}
      <path d="M194 88 Q 214 82 238 74 Q 218 92 196 102 Z" fill="#e8352f" />
      <path d="M230 77 L 238 74 L 233 82 Z" fill="#111" />

      {/* big friendly eye */}
      <circle cx="170" cy="90" r="18" fill="#fff" />
      <circle cx="174" cy={92 + look} r="12" fill="#111" />
      <circle cx="178.5" cy={86 + look} r="4.2" fill="#fff" />
      <circle cx="170" cy={97 + look} r="1.8" fill="#fff" />

      {/* blush and smile */}
      <circle cx="186" cy="116" r="7" fill="#ff8a80" opacity=".8" />
      {mood === "think"
        ? <path d="M168 120 h 9" stroke="#111" strokeWidth="2.6" strokeLinecap="round" />
        : <path d="M166 118 q 6 6 13 1" stroke="#111" strokeWidth="2.6" fill="none" strokeLinecap="round" />}
    </svg>
  );
}
