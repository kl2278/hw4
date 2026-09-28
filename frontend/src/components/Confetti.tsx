import { useMemo } from "react";
import "./Confetti.css";

const COLORS = ["var(--accent)", "var(--soft-blue-deep)", "var(--navy)", "var(--cream-deep)"];

interface Piece {
  left: number;
  delay: number;
  duration: number;
  rotation: number;
  color: string;
}

export default function Confetti() {
  const reduceMotion =
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const pieces = useMemo<Piece[]>(() => {
    if (reduceMotion) return [];
    return Array.from({ length: 36 }, () => ({
      left: Math.random() * 100,
      delay: Math.random() * 0.4,
      duration: 1.8 + Math.random() * 1.2,
      rotation: Math.random() * 360,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
    }));
  }, [reduceMotion]);

  if (reduceMotion) return null;

  return (
    <div className="confetti" aria-hidden="true">
      {pieces.map((p, i) => (
        <span
          key={i}
          className="confetti-piece"
          style={{
            left: `${p.left}%`,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            background: p.color,
            transform: `rotate(${p.rotation}deg)`,
          }}
        />
      ))}
    </div>
  );
}
