// Deterministic per-product "collage" styling (size/tilt/tape color) derived
// from the product_id, so the layout looks scattered but stays stable across
// re-renders, filter changes, and re-sorts instead of reshuffling randomly.

const SIZES = ["a", "a", "a", "a", "b"]; // "b" (larger) is intentionally rare
const TILTS = ["tilt-1", "tilt-2", "tilt-3", "tilt-4"];
const TAPES = ["tape-blue", "tape-cream", "tape-coral"];

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export interface CardVariant {
  size: string;
  tilt: string;
  tape: string;
}

export function cardVariant(productId: string): CardVariant {
  const h = hashString(productId);
  return {
    size: SIZES[h % SIZES.length],
    tilt: TILTS[Math.floor(h / SIZES.length) % TILTS.length],
    tape: TAPES[Math.floor(h / (SIZES.length * TILTS.length)) % TAPES.length],
  };
}
