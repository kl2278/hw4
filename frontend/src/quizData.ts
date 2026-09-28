import type { ProductSummary } from "./api";
import { categoryFor } from "./productCategory";

export interface QuizOption {
  label: string;
  category?: string;
  color?: string;
  priceBand?: "low" | "mid" | "high";
  repStyle?: "college" | "sport" | "grad";
}

export interface QuizQuestion {
  prompt: string;
  options: QuizOption[];
}

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    prompt: "Your ideal Saturday?",
    options: [
      { label: "Tailgating at the Bowl", category: "Quarter-Zips" },
      { label: "Curled up in the library", category: "Crewnecks" },
      { label: "Brunch with the squad", category: "T-Shirts" },
      { label: "Napping in something cozy", category: "Hoodies" },
    ],
  },
  {
    prompt: "Pick a vibe.",
    options: [
      { label: "Classic & preppy", category: "Quarter-Zips" },
      { label: "Oversized & cozy", category: "Hoodies" },
      { label: "Clean & simple", category: "T-Shirts" },
      { label: "Timeless varsity", category: "Crewnecks" },
    ],
  },
  {
    prompt: "Pick a color mood.",
    options: [
      { label: "Yale Blue, always", color: "navy" },
      { label: "Heather gray, low-key", color: "gray" },
      { label: "Crisp white", color: "white" },
      { label: "Surprise me", color: undefined },
    ],
  },
  {
    prompt: "How do you rep Yale?",
    options: [
      { label: "My residential college", repStyle: "college" },
      { label: "My varsity sport", repStyle: "sport" },
      { label: "My grad program", repStyle: "grad", priceBand: "high" },
      { label: "However feels right", repStyle: undefined },
    ],
  },
];

export interface QuizProfile {
  category?: string;
  color?: string;
  priceBand?: "low" | "mid" | "high";
  repStyle?: "college" | "sport" | "grad";
}

const SPORT_WORDS = [
  "hockey", "soccer", "baseball", "football", "lacrosse", "sailing", "tennis",
  "golf", "volleyball", "swimming", "fencing", "squash", "crew", "diving",
  "basketball", "track", "field",
];

function priceBandThresholds(products: ProductSummary[]): [number, number] {
  const prices = [...products.map((p) => p.price)].sort((a, b) => a - b);
  if (prices.length === 0) return [0, 0];
  const low = prices[Math.floor(prices.length / 3)];
  const high = prices[Math.floor((prices.length * 2) / 3)];
  return [low, high];
}

function bandFor(price: number, [low, high]: [number, number]): "low" | "mid" | "high" {
  if (price <= low) return "low";
  if (price >= high) return "high";
  return "mid";
}

function scoreProduct(product: ProductSummary, profile: QuizProfile, bands: [number, number]): number {
  let score = 0;
  const text = `${product.name} ${product.description}`.toLowerCase();

  if (profile.category && categoryFor(product.garment_type) === profile.category) score += 3;
  if (profile.color && product.colors.some((c) => c.toLowerCase().includes(profile.color!))) score += 2;
  if (profile.priceBand && bandFor(product.price, bands) === profile.priceBand) score += 1;
  if (profile.repStyle === "college" && text.includes("college")) score += 2;
  if (profile.repStyle === "grad" && text.includes("school of")) score += 2;
  if (profile.repStyle === "sport" && SPORT_WORDS.some((w) => text.includes(w))) score += 2;

  return score;
}

/** Picks 3 real catalogue products best matching the quiz answers. Every value
 * shown (name, price, image, link) comes straight from `products` — nothing
 * here is invented.
 */
export function recommendProducts(
  products: ProductSummary[],
  profile: QuizProfile,
  count = 3,
): ProductSummary[] {
  const bands = priceBandThresholds(products);
  const scored = products
    .map((p) => ({ product: p, score: scoreProduct(p, profile, bands) }))
    .sort((a, b) => b.score - a.score);

  // Shuffle within the top tier so repeat quiz-takers don't always see the
  // exact same 3 products for a given answer combination.
  const topScore = scored[0]?.score ?? 0;
  const top = scored.filter((s) => s.score === topScore);
  for (let i = top.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [top[i], top[j]] = [top[j], top[i]];
  }
  const rest = scored.filter((s) => s.score !== topScore);

  return [...top, ...rest].slice(0, count).map((s) => s.product);
}
