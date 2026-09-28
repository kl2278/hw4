// An original, simplified cartoon bulldog face for the chat assistant's avatar —
// drawn as plain geometric shapes in inline SVG, not a photo or Yale's mascot art.
export default function BoolaAvatar({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" role="img">
      <circle cx="32" cy="32" r="32" fill="var(--soft-blue)" />
      <ellipse cx="13" cy="27" rx="8" ry="13" fill="var(--navy)" transform="rotate(-18 13 27)" />
      <ellipse cx="51" cy="27" rx="8" ry="13" fill="var(--navy)" transform="rotate(18 51 27)" />
      <ellipse cx="32" cy="37" rx="19" ry="15" fill="#f4ede1" />
      <ellipse cx="32" cy="43" rx="10" ry="7" fill="#ffffff" />
      <circle cx="24" cy="31" r="3" fill="var(--navy)" />
      <circle cx="40" cy="31" r="3" fill="var(--navy)" />
      <ellipse cx="32" cy="39" rx="3" ry="2.2" fill="var(--navy)" />
      <path
        d="M26 45 Q32 50 38 45"
        stroke="var(--navy)"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}
