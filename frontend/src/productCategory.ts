// The catalogue's garment_type field is messy free text ("full-zip hooded sweatshirt",
// "quarter-zip pullover sweatshirt", "short-sleeve T-shirt", ...). This buckets it into a
// small set of categories a shopper would actually filter by.
const CATEGORY_ORDER = ["Hoodies", "Crewnecks", "Quarter-Zips", "Jackets", "T-Shirts", "Long-Sleeves", "Other"];

export function categoryFor(garmentType: string): string {
  const g = garmentType.toLowerCase();
  if (g.includes("quarter-zip")) return "Quarter-Zips";
  if (g.includes("hood")) return "Hoodies";
  if (g.includes("jacket")) return "Jackets";
  if (g.includes("crewneck") || g.includes("mockneck")) return "Crewnecks";
  if (g.includes("t-shirt") || g.includes("tee")) return "T-Shirts";
  if (g.includes("long-sleeve")) return "Long-Sleeves";
  return "Other";
}

export function sortCategories(categories: Iterable<string>): string[] {
  const set = new Set(categories);
  return CATEGORY_ORDER.filter((c) => set.has(c));
}
