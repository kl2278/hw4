import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProducts, type ChatProductCard, type ProductSummary } from "../api";
import { useChatResults } from "../chatResults";
import { categoryFor, sortCategories } from "../productCategory";
import { cardVariant } from "../cardVariant";
import { useReveal } from "../useReveal";
import "./Products.css";

const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];

type SortOrder = "none" | "price-asc" | "price-desc";

function ProductGridCard({ product }: { product: ChatProductCard }) {
  const { ref, visible } = useReveal<HTMLAnchorElement>();
  const variant = cardVariant(product.product_id);
  const classes = [
    "product-card",
    "reveal",
    visible ? "in-view" : "",
    `card-size-${variant.size}`,
    variant.tilt,
    variant.tape,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Link ref={ref} to={`/products/${product.product_id}`} className={classes}>
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} />
      </div>
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="product-price">${product.price.toFixed(2)}</p>
        <p className="product-desc">{product.description}</p>
      </div>
    </Link>
  );
}

export default function Products() {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState("All");
  const [size, setSize] = useState("Any");
  const [sort, setSort] = useState<SortOrder>("none");
  const { results, clearResults } = useChatResults();

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("Couldn't load products. Is the backend running?"));
  }, []);

  const categories = useMemo(() => sortCategories(products.map((p) => categoryFor(p.garment_type))), [products]);

  const displayed: ChatProductCard[] = results ? results.products : products;

  const filtered = useMemo(() => {
    let list = displayed;
    if (category !== "All") {
      list = list.filter((p) => categoryFor(p.garment_type) === category);
    }
    if (size !== "Any") {
      list = list.filter((p) => p.in_stock_sizes.includes(size));
    }
    if (sort !== "none") {
      list = [...list].sort((a, b) => (sort === "price-asc" ? a.price - b.price : b.price - a.price));
    }
    return list;
  }, [displayed, category, size, sort]);

  if (error) return <p className="products-error">{error}</p>;

  return (
    <div className="products-page">
      <h1>Products</h1>
      {results && (
        <div className="products-filter-banner">
          <span>
            Showing results for: <strong>{results.query}</strong>
          </span>
          <button onClick={clearResults}>Clear</button>
        </div>
      )}
      <div className="products-toolbar">
        <label>
          Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="All">All</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label>
          Size in stock
          <select value={size} onChange={(e) => setSize(e.target.value)}>
            <option value="Any">Any</option>
            {SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Sort by price
          <select value={sort} onChange={(e) => setSort(e.target.value as SortOrder)}>
            <option value="none">Default</option>
            <option value="price-asc">Low to high</option>
            <option value="price-desc">High to low</option>
          </select>
        </label>
      </div>
      {filtered.length === 0 ? (
        <p className="products-empty">No products match those filters.</p>
      ) : (
        <div className="product-grid">
          {filtered.map((p) => (
            <ProductGridCard key={p.product_id} product={p} />
          ))}
        </div>
      )}
    </div>
  );
}
